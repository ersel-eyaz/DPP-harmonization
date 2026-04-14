from __future__ import annotations

from dataclasses import dataclass
import math
import re

from jsonld_ingestor import ingest_jsonld_document
from registry import FLAT_FIELD_DEFINITIONS, CanonicalFieldDefinition
from sample_jsonld_data import EXAMPLE_JSONLD_DOCUMENT
from schemas import RawObservation


# Feature-based suggestion sandbox for semantic field matching.
# It builds canonical candidates from the registry, converts raw observations
# into structured queries, extracts lightweight ranking features, and scores
# candidates with a weighted combination of lexical, unit, and context signals.
#
# This module remains a fallback suggestion layer rather than the main resolver.
# Hard constraints such as entity filtering still belong to the harmonizer.
# However, compared to the previous version, the ranking now uses multiple
# explicit features instead of a single lexical overlap score.


@dataclass(slots=True)
class CanonicalCandidate:
    concept_name: str
    target_field: str
    entity_type: str
    description: str
    aliases: tuple[str, ...]
    source_model: str
    source_field: str
    core_text_representation: str
    context_text_representation: str


@dataclass(slots=True)
class ObservationQuery:
    raw_label: str
    entity_type: str
    entity_id: str | None
    raw_unit: str | None
    source_system: str | None
    source_node_type: str | None
    source_path: str | None
    neighbor_labels: list[str]
    core_text_representation: str
    context_text_representation: str


@dataclass(slots=True)
class CandidateFeatures:
    alias_exact_match: float
    source_field_exact_match: float
    alias_normalized_match: float
    source_field_normalized_match: float
    token_overlap: float
    char_ngram_similarity: float
    unit_compatibility: float
    source_node_type_match: float
    entity_name_match_from_node_type: float
    neighbor_overlap: float
    context_similarity: float


@dataclass(slots=True)
class ScoredCandidate:
    candidate: CanonicalCandidate
    score: float
    features: CandidateFeatures


def _split_camel_case(text: str) -> str:
    """
    Insert spaces into camelCase / PascalCase strings.

    Example:
    - runtimeHours -> runtime Hours
    - massGram -> mass Gram
    - GHGEmissionRecord -> GHG Emission Record
    """
    step1 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    step2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", step1)
    return step2


def _normalize_token(token: str) -> str:
    """
    Apply lightweight token normalization.

    This remains intentionally simple:
    - lowercase
    - singularize a few common plural forms
    - normalize a few domain-relevant near-synonyms
    """
    token = token.lower().strip()

    plural_map = {
        "grams": "gram",
        "grams.": "gram",
        "hours": "hour",
        "hrs": "hour",
        "hr": "hour",
        "events": "event",
        "cycles": "cycle",
        "kilometers": "kilometer",
        "kms": "kilometer",
        "counts": "count",
        "percentages": "percent",
    }
    token = plural_map.get(token, token)

    synonym_map = {
        "runtime": "operating",
        "usage": "operating",
        "operate": "operating",
        "operation": "operating",
        "mass": "weight",
        "weighted": "weight",
        "travel": "transport",
        "route": "transport",
        "distance": "distance",
        "carbon": "ghg",
        "co2": "ghg",
        "co2e": "ghg",
        "emission": "ghg",
        "emissions": "ghg",
        "descale": "descaling",
        "descaling": "descaling",
        "chalk": "descaling",
        "brew": "brewing",
        "brews": "brewing",
        "cleanings": "cleaning",
        "purity": "purity",
        "recycled": "recycled",
    }
    token = synonym_map.get(token, token)

    return token


def normalize_for_similarity(text: str) -> list[str]:
    """
    Normalize text into comparable lexical tokens.

    Behavior:
    - split camelCase / PascalCase
    - treat underscores and hyphens as separators
    - lowercase
    - extract alphanumeric tokens
    - apply light normalization
    """
    if not text:
        return []

    split_text = _split_camel_case(text)
    normalized = split_text.replace("_", " ").replace("-", " ")
    raw_tokens = re.findall(r"[a-zA-Z0-9]+", normalized)

    tokens = [_normalize_token(token) for token in raw_tokens]
    return [token for token in tokens if token]


def _normalize_text(text: str) -> str:
    """
    Normalize text into a compact comparable string.
    """
    return " ".join(normalize_for_similarity(text)).strip()


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    compact = re.sub(r"\s+", "", _normalize_text(text))
    if not compact:
        return set()
    if len(compact) < n:
        return {compact}
    return {compact[index:index + n] for index in range(len(compact) - n + 1)}


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _max_token_overlap_ratio(query_tokens: set[str], candidate_token_sets: list[set[str]]) -> float:
    """
    Compare the observation label against multiple candidate label surfaces
    and return the strongest token-overlap signal.
    """
    if not query_tokens:
        return 0.0

    best = 0.0
    for token_set in candidate_token_sets:
        if not token_set:
            continue
        overlap_ratio = len(query_tokens & token_set) / len(query_tokens)
        if overlap_ratio > best:
            best = overlap_ratio

    return best


def _max_char_ngram_similarity(query_label: str, candidate_surfaces: list[str]) -> float:
    """
    Compare the observation label against multiple candidate label surfaces
    using character trigrams.
    """
    query_ngrams = _char_ngrams(query_label)
    if not query_ngrams:
        return 0.0

    best = 0.0
    for surface in candidate_surfaces:
        surface_ngrams = _char_ngrams(surface)
        similarity = _jaccard_similarity(query_ngrams, surface_ngrams)
        if similarity > best:
            best = similarity

    return best


def lexical_similarity_score(query_text: str, candidate_text: str) -> float:
    """
    Backward-compatible lexical similarity helper.

    This now uses Jaccard similarity over normalized token sets instead of the
    earlier overlap/query-size ratio.
    """
    query_tokens = set(normalize_for_similarity(query_text))
    candidate_tokens = set(normalize_for_similarity(candidate_text))
    return _jaccard_similarity(query_tokens, candidate_tokens)


def _normalize_unit_token(unit: str | None) -> str | None:
    if not unit:
        return None

    normalized = _normalize_text(unit)

    unit_map = {
        "h": "h",
        "hour": "h",
        "count": "count",
        "cycle": "count",
        "event": "count",
        "g": "g",
        "gram": "g",
        "percent": "%",
        "km": "km",
        "kilometer": "km",
        "kg ghg": "kg_co2e",
        "kg co2e": "kg_co2e",
        "kgco2e": "kg_co2e",
        "kg co 2 e": "kg_co2e",
    }
    return unit_map.get(normalized, normalized)


def _infer_expected_unit_from_candidate(candidate: CanonicalCandidate) -> str | None:
    normalized = _normalize_text(candidate.core_text_representation)

    if "kg co2e" in normalized or "kg ghg" in normalized:
        return "kg_co2e"
    if " kilometer " in f" {normalized} " or normalized.endswith(" kilometer") or normalized.endswith(" km"):
        return "km"
    if " percent " in f" {normalized} ":
        return "%"
    if " gram " in f" {normalized} " or normalized.endswith(" g"):
        return "g"
    if " hour " in f" {normalized} " or normalized.endswith(" h"):
        return "h"
    if " count " in f" {normalized} ":
        return "count"

    return None


def _compute_unit_compatibility(raw_unit: str | None, candidate: CanonicalCandidate) -> float:
    normalized_raw_unit = _normalize_unit_token(raw_unit)
    expected_unit = _infer_expected_unit_from_candidate(candidate)

    if normalized_raw_unit is None:
        return 0.0

    if expected_unit is None:
        return 0.0

    if normalized_raw_unit == expected_unit:
        return 1.0

    count_equivalents = {"count"}
    if normalized_raw_unit in count_equivalents and expected_unit in count_equivalents:
        return 1.0

    return 0.0


def build_candidate_core_text(definition: CanonicalFieldDefinition) -> str:
    """
    Build the text used directly for lexical ranking.
    """
    parts = [
        definition.canonical_concept.value,
        definition.target_field,
        definition.entity_type.value,
        definition.source_field,
        *definition.allowed_raw_labels,
    ]
    return " ".join(part for part in parts if part).strip()


def build_candidate_context_text(definition: CanonicalFieldDefinition) -> str:
    """
    Build auxiliary context text for context-level similarity.
    """
    parts = [
        definition.source_model,
        definition.description,
    ]
    return " ".join(part for part in parts if part).strip()


def build_canonical_candidates() -> list[CanonicalCandidate]:
    candidates: list[CanonicalCandidate] = []

    for definition in FLAT_FIELD_DEFINITIONS:
        core_text_representation = build_candidate_core_text(definition)
        context_text_representation = build_candidate_context_text(definition)

        candidates.append(
            CanonicalCandidate(
                concept_name=definition.canonical_concept.value,
                target_field=definition.target_field,
                entity_type=definition.entity_type.value,
                description=definition.description,
                aliases=definition.allowed_raw_labels,
                source_model=definition.source_model,
                source_field=definition.source_field,
                core_text_representation=core_text_representation,
                context_text_representation=context_text_representation,
            )
        )

    return candidates


def build_observation_query(observation: RawObservation) -> ObservationQuery:
    """
    Build a structured query representation from a raw observation.

    The core text remains label-centered.
    The context text keeps lightweight node and neighborhood metadata.
    """
    core_parts = [observation.raw_label]

    if observation.raw_unit:
        core_parts.append(observation.raw_unit)

    context_parts = [observation.entity_type.value]

    if observation.source_node_type:
        context_parts.append(observation.source_node_type)

    if observation.entity_id:
        context_parts.append(observation.entity_id)

    if observation.source_system:
        context_parts.append(observation.source_system)

    if observation.source_path:
        context_parts.append(observation.source_path)

    context_parts.extend(observation.neighbor_labels)

    return ObservationQuery(
        raw_label=observation.raw_label,
        entity_type=observation.entity_type.value,
        entity_id=observation.entity_id,
        raw_unit=observation.raw_unit,
        source_system=observation.source_system,
        source_node_type=observation.source_node_type,
        source_path=observation.source_path,
        neighbor_labels=observation.neighbor_labels,
        core_text_representation=" ".join(core_parts).strip(),
        context_text_representation=" ".join(context_parts).strip(),
    )


def extract_candidate_features(
    query: ObservationQuery,
    candidate: CanonicalCandidate,
) -> CandidateFeatures:
    """
    Extract explicit ranking features for one observation-candidate pair.
    """
    normalized_raw_label = _normalize_text(query.raw_label)
    normalized_source_field = _normalize_text(candidate.source_field)
    normalized_aliases = {_normalize_text(alias) for alias in candidate.aliases}
    normalized_neighbor_labels = {_normalize_text(label) for label in query.neighbor_labels if label.strip()}

    candidate_surfaces = [candidate.source_field, *candidate.aliases]
    candidate_token_sets = [set(normalize_for_similarity(surface)) for surface in candidate_surfaces]
    query_label_tokens = set(normalize_for_similarity(query.raw_label))

    alias_exact_match = 1.0 if query.raw_label in candidate.aliases else 0.0
    source_field_exact_match = 1.0 if query.raw_label == candidate.source_field else 0.0
    alias_normalized_match = 1.0 if normalized_raw_label in normalized_aliases else 0.0
    source_field_normalized_match = 1.0 if normalized_raw_label == normalized_source_field else 0.0

    token_overlap = _max_token_overlap_ratio(query_label_tokens, candidate_token_sets)
    char_ngram_similarity = _max_char_ngram_similarity(query.raw_label, candidate_surfaces)

    unit_compatibility = _compute_unit_compatibility(query.raw_unit, candidate)

    source_node_type_match = 0.0
    entity_name_match_from_node_type = 0.0
    if query.source_node_type:
        normalized_node_type = _normalize_text(query.source_node_type)

        if normalized_node_type == _normalize_text(candidate.source_model):
            source_node_type_match = 1.0

        if normalized_node_type == _normalize_text(candidate.entity_type):
            entity_name_match_from_node_type = 1.0

    candidate_context_labels = {
        _normalize_text(candidate.source_field),
        *normalized_aliases,
    }

    if normalized_neighbor_labels:
        neighbor_overlap = len(normalized_neighbor_labels & candidate_context_labels) / len(normalized_neighbor_labels)
    else:
        neighbor_overlap = 0.0

    context_similarity = lexical_similarity_score(
        query_text=query.context_text_representation,
        candidate_text=candidate.context_text_representation,
    )

    return CandidateFeatures(
        alias_exact_match=alias_exact_match,
        source_field_exact_match=source_field_exact_match,
        alias_normalized_match=alias_normalized_match,
        source_field_normalized_match=source_field_normalized_match,
        token_overlap=token_overlap,
        char_ngram_similarity=char_ngram_similarity,
        unit_compatibility=unit_compatibility,
        source_node_type_match=source_node_type_match,
        entity_name_match_from_node_type=entity_name_match_from_node_type,
        neighbor_overlap=neighbor_overlap,
        context_similarity=context_similarity,
    )


def score_candidate(features: CandidateFeatures) -> float:
    """
    Weighted feature-based candidate scoring.

    The weights are intentionally heuristic and conservative:
    - exact/normalized label matches dominate
    - lexical evidence remains important
    - unit/context features support ranking but do not fully override label evidence
    """
    score = (
        0.24 * features.alias_exact_match
        + 0.20 * features.source_field_exact_match
        + 0.12 * features.alias_normalized_match
        + 0.08 * features.source_field_normalized_match
        + 0.18 * features.token_overlap
        + 0.08 * features.char_ngram_similarity
        + 0.05 * features.unit_compatibility
        + 0.025 * features.source_node_type_match
        + 0.015 * features.entity_name_match_from_node_type
        + 0.035 * features.neighbor_overlap
        + 0.015 * features.context_similarity
    )

    return round(min(1.0, max(0.0, score)), 6)


def rank_candidates(
    query: ObservationQuery,
    candidates: list[CanonicalCandidate],
) -> list[ScoredCandidate]:
    """
    Rank canonical candidates with explicit feature-based scoring.

    This remains a lightweight fallback mechanism.
    """
    scored: list[ScoredCandidate] = []

    for candidate in candidates:
        features = extract_candidate_features(query, candidate)
        score = score_candidate(features)
        scored.append(
            ScoredCandidate(
                candidate=candidate,
                score=score,
                features=features,
            )
        )

    scored.sort(
        key=lambda item: (
            -item.score,
            -item.features.alias_exact_match,
            -item.features.source_field_exact_match,
            -item.features.alias_normalized_match,
            -item.features.token_overlap,
            item.candidate.entity_type,
            item.candidate.concept_name,
            item.candidate.source_field,
        )
    )
    return scored


def demo_similarity_inputs() -> None:
    print("Building canonical candidates...")
    candidates = build_canonical_candidates()
    print(f"Total candidates: {len(candidates)}")
    print()

    for candidate in candidates:
        print("Canonical candidate:")
        print(f"  concept_name: {candidate.concept_name}")
        print(f"  target_field: {candidate.target_field}")
        print(f"  entity_type: {candidate.entity_type}")
        print(f"  source_model: {candidate.source_model}")
        print(f"  source_field: {candidate.source_field}")
        print(f"  aliases: {candidate.aliases}")
        print(f"  core_text_representation: {candidate.core_text_representation}")
        print(f"  context_text_representation: {candidate.context_text_representation}")
        print()

    print("Ingesting JSON-LD document...")
    raw_dataset = ingest_jsonld_document(EXAMPLE_JSONLD_DOCUMENT, source_system="jsonld_demo")
    print(f"Extracted raw observations: {len(raw_dataset.observations)}")
    print()

    print("Building observation queries and feature-based suggestions...")
    for observation in raw_dataset.observations:
        query = build_observation_query(observation)
        ranked = rank_candidates(query, candidates)

        print("Observation query:")
        print(f"  raw_label: {query.raw_label}")
        print(f"  entity_type: {query.entity_type}")
        print(f"  entity_id: {query.entity_id}")
        print(f"  raw_unit: {query.raw_unit}")
        print(f"  source_system: {query.source_system}")
        print(f"  source_node_type: {query.source_node_type}")
        print(f"  source_path: {query.source_path}")
        print(f"  neighbor_labels: {query.neighbor_labels}")
        print(f"  core_text_representation: {query.core_text_representation}")
        print(f"  context_text_representation: {query.context_text_representation}")
        print("  top_candidates:")

        for item in ranked[:3]:
            candidate = item.candidate
            features = item.features
            print(
                "    - "
                f"concept={candidate.concept_name}, "
                f"target_field={candidate.target_field}, "
                f"entity_type={candidate.entity_type}, "
                f"source_field={candidate.source_field}, "
                f"score={item.score:.3f}, "
                f"token_overlap={features.token_overlap:.3f}, "
                f"char_ngram_similarity={features.char_ngram_similarity:.3f}, "
                f"unit_compatibility={features.unit_compatibility:.3f}, "
                f"neighbor_overlap={features.neighbor_overlap:.3f}"
            )

        print()


if __name__ == "__main__":
    demo_similarity_inputs()