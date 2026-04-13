from __future__ import annotations

from dataclasses import dataclass
import re

from jsonld_ingestor import ingest_jsonld_document
from registry import FLAT_FIELD_DEFINITIONS, CanonicalFieldDefinition
from sample_jsonld_data import EXAMPLE_JSONLD_DOCUMENT
from schemas import RawObservation


# Lightweight suggestion sandbox for semantic field matching.
# It builds canonical candidate descriptions from the registry, converts raw
# observations into textual queries, and ranks candidates with a simple
# lexical overlap score.
#
# This module is intentionally not the main harmonization resolver.
# Structured signals such as entity type, units, and other hard constraints
# should be handled by the rule-based harmonization pipeline. Here, they are
# kept mainly for inspection, debugging, and fallback suggestion generation.


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
class ScoredCandidate:
    candidate: CanonicalCandidate
    score: float


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

    This is intentionally simple:
    - lowercase
    - singularize a few common plural forms
    - normalize a few domain-relevant near-synonyms
    """
    token = token.lower().strip()

    plural_map = {
        "grams": "gram",
        "hours": "hour",
        "events": "event",
        "cycles": "cycle",
        "kilometers": "kilometer",
        "counts": "count",
    }
    token = plural_map.get(token, token)

    synonym_map = {
        "hrs": "hour",
        "hr": "hour",
        "runtime": "operating",
        "mass": "weight",
        "travel": "transport",
        "carbon": "ghg",
        "co2e": "ghg",
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
    split_text = _split_camel_case(text)
    normalized = split_text.replace("_", " ").replace("-", " ")
    raw_tokens = re.findall(r"[a-zA-Z0-9]+", normalized)

    tokens = [_normalize_token(token) for token in raw_tokens]
    return [token for token in tokens if token]


def lexical_similarity_score(query_text: str, candidate_text: str) -> float:
    """
    Compute a simple token-overlap score.

    Score = overlap / number of unique query tokens
    """
    query_tokens = set(normalize_for_similarity(query_text))
    candidate_tokens = set(normalize_for_similarity(candidate_text))

    if not query_tokens:
        return 0.0

    overlap = query_tokens & candidate_tokens
    return len(overlap) / len(query_tokens)


def rank_candidates(
    query: ObservationQuery,
    candidates: list[CanonicalCandidate],
) -> list[ScoredCandidate]:
    """
    Rank all canonical candidates by lexical similarity only.

    This ranking is deliberately generic and should be interpreted as a
    suggestion mechanism, not as the final harmonization decision.
    """
    scored: list[ScoredCandidate] = []

    for candidate in candidates:
        score = lexical_similarity_score(
            query_text=query.core_text_representation,
            candidate_text=candidate.core_text_representation,
        )
        scored.append(ScoredCandidate(candidate=candidate, score=score))

    scored.sort(
        key=lambda item: (
            -item.score,
            item.candidate.entity_type,
            item.candidate.concept_name,
            item.candidate.source_field,
        )
    )
    return scored


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


def build_candidate_core_text(definition: CanonicalFieldDefinition) -> str:
    """
    Build the text used directly for lexical suggestion ranking.
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
    Build auxiliary context text kept for debugging or future experiments.
    """
    parts = [
        definition.source_model,
        definition.description,
    ]
    return " ".join(part for part in parts if part).strip()


def build_observation_query(observation: RawObservation) -> ObservationQuery:
    """
    Build a query representation from a raw observation.

    The core text stays intentionally compact and label-centered because this
    module is treated as a fallback suggestion tool rather than the main
    structured resolver.

    Contextual metadata is still preserved for inspection and future
    experiments.
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

    print("Building observation queries and lexical suggestions...")
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
            print(
                "    - "
                f"concept={candidate.concept_name}, "
                f"target_field={candidate.target_field}, "
                f"entity_type={candidate.entity_type}, "
                f"source_field={candidate.source_field}, "
                f"score={item.score:.3f}"
            )

        print()


if __name__ == "__main__":
    demo_similarity_inputs()