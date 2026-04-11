from __future__ import annotations

from dataclasses import dataclass
import re

from jsonld_ingestor import ingest_jsonld_document
from registry import FLAT_FIELD_DEFINITIONS, CanonicalFieldDefinition
from sample_jsonld_data import EXAMPLE_JSONLD_DOCUMENT
from schemas import RawObservation


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
    core_text_representation: str
    context_text_representation: str


@dataclass(slots=True)
class ScoredCandidate:
    candidate: CanonicalCandidate
    score: float


def normalize_for_similarity(text: str) -> list[str]:
    """
    Lowercases text and extracts simple alphanumeric tokens.
    Underscores are treated as separators.
    """
    normalized = text.lower().replace("_", " ")
    return re.findall(r"[a-z0-9]+", normalized)


def lexical_similarity_score(query_text: str, candidate_text: str) -> float:
    """
    Very simple token-overlap score.

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
    scored: list[ScoredCandidate] = []

    for candidate in candidates:
        score = lexical_similarity_score(
            query_text=query.core_text_representation,
            candidate_text=candidate.core_text_representation,
        )
        scored.append(ScoredCandidate(candidate=candidate, score=score))

    scored.sort(key=lambda item: item.score, reverse=True)
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
    Core fields used directly for the current lexical ranking.
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
    Context fields kept for future experiments or debugging,
    but not used in the current score yet.
    """
    parts = [
        definition.source_model,
        definition.description,
    ]
    return " ".join(part for part in parts if part).strip()


def build_observation_query(observation: RawObservation) -> ObservationQuery:
    core_parts = [
        observation.raw_label,
        observation.entity_type.value,
    ]

    if observation.raw_unit:
        core_parts.append(observation.raw_unit)

    context_parts = []

    if observation.entity_id:
        context_parts.append(observation.entity_id)

    if observation.source_system:
        context_parts.append(observation.source_system)

    return ObservationQuery(
        raw_label=observation.raw_label,
        entity_type=observation.entity_type.value,
        entity_id=observation.entity_id,
        raw_unit=observation.raw_unit,
        source_system=observation.source_system,
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
    raw_dataset = ingest_jsonld_document(
        EXAMPLE_JSONLD_DOCUMENT,
        source_system="jsonld_demo",
    )
    print(f"Extracted raw observations: {len(raw_dataset.observations)}")
    print()

    print("Building observation queries and ranking candidates...")
    for observation in raw_dataset.observations:
        query = build_observation_query(observation)
        ranked = rank_candidates(query, candidates)

        print("Observation query:")
        print(f"  raw_label: {query.raw_label}")
        print(f"  entity_type: {query.entity_type}")
        print(f"  entity_id: {query.entity_id}")
        print(f"  raw_unit: {query.raw_unit}")
        print(f"  source_system: {query.source_system}")
        print(f"  core_text_representation: {query.core_text_representation}")
        print(f"  context_text_representation: {query.context_text_representation}")
        print("  top_candidates:")

        for item in ranked[:5]:
            print(
                f"    - concept={item.candidate.concept_name}, "
                f"target_field={item.candidate.target_field}, "
                f"entity_type={item.candidate.entity_type}, "
                f"source_field={item.candidate.source_field}, "
                f"score={item.score:.3f}"
            )

        print()


if __name__ == "__main__":
    demo_similarity_inputs()