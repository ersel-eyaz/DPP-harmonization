# This module contains small helper functions for the sandbox.
# It provides access to the canonical field registry and simple lookup utilities
# that can be reused by later harmonization components.
# The helpers now support multiple field definitions per canonical concept.

from typing import Any

from enums import CanonicalConcept
from registry import (
    CANONICAL_FIELD_REGISTRY,
    FLAT_FIELD_DEFINITIONS,
    CanonicalFieldDefinition,
)
from schemas import HarmonizationRecord


class RegistryLookupError(ValueError):
    pass


def get_definitions(concept: CanonicalConcept) -> tuple[CanonicalFieldDefinition, ...]:
    try:
        return CANONICAL_FIELD_REGISTRY[concept]
    except KeyError as exc:
        raise RegistryLookupError(f"Unknown canonical concept: {concept}") from exc


def get_definition_count(concept: CanonicalConcept) -> int:
    return len(get_definitions(concept))


def list_canonical_concepts() -> list[str]:
    return [concept.value for concept in CanonicalConcept]


def list_allowed_raw_labels() -> dict[str, tuple[str, ...]]:
    """
    Returns all allowed raw labels grouped by canonical concept.

    Since a concept can now have multiple field definitions, labels from all
    matching definitions are merged into a single tuple per concept.
    """
    grouped_labels: dict[str, list[str]] = {}

    for concept, definitions in CANONICAL_FIELD_REGISTRY.items():
        concept_name = concept.value
        grouped_labels.setdefault(concept_name, [])

        for definition in definitions:
            grouped_labels[concept_name].extend(definition.allowed_raw_labels)

    deduplicated: dict[str, tuple[str, ...]] = {}

    for concept_name, labels in grouped_labels.items():
        unique_labels = tuple(dict.fromkeys(labels))
        deduplicated[concept_name] = unique_labels

    return deduplicated


def list_flat_definitions() -> tuple[CanonicalFieldDefinition, ...]:
    return FLAT_FIELD_DEFINITIONS


def build_empty_harmonization_record(
    raw_label: str,
    raw_value: Any,
    concept: CanonicalConcept,
    confidence: float = 0.0,
) -> HarmonizationRecord:
    """
    Builds an empty harmonization record using the first definition registered
    for the given canonical concept.

    This helper remains convenient for concept-level utilities, even though
    a concept may now have multiple source field definitions.
    """
    definitions = get_definitions(concept)
    definition = definitions[0]

    return HarmonizationRecord(
        raw_label=raw_label,
        raw_value=raw_value,
        canonical_concept=definition.canonical_concept,
        target_field=definition.target_field,
        normalized_value=None,
        normalized_unit=definition.normalized_unit.value,
        confidence=confidence,
    )