# This module contains small helper functions for the sandbox.
# It provides access to the canonical field registry and simple lookup utilities
# that can be reused by later harmonization components.
# At this stage, the helpers support structure and consistency, not full harmonization.

from typing import Any

from enums import CanonicalConcept
from registry import CANONICAL_FIELD_REGISTRY, CanonicalFieldDefinition
from schemas import HarmonizationRecord


class RegistryLookupError(ValueError):
    pass


def get_definition(concept: CanonicalConcept) -> CanonicalFieldDefinition:
    try:
        return CANONICAL_FIELD_REGISTRY[concept]
    except KeyError as exc:
        raise RegistryLookupError(f"Unknown canonical concept: {concept}") from exc


def list_canonical_concepts() -> list[str]:
    return [concept.value for concept in CanonicalConcept]


def list_allowed_raw_labels() -> dict[str, tuple[str, ...]]:
    return {
        concept.value: definition.allowed_raw_labels
        for concept, definition in CANONICAL_FIELD_REGISTRY.items()
    }


def build_empty_harmonization_record(
    raw_label: str,
    raw_value: Any,
    concept: CanonicalConcept,
    confidence: float = 0.0,
) -> HarmonizationRecord:
    definition = get_definition(concept)
    return HarmonizationRecord(
        raw_label=raw_label,
        raw_value=raw_value,
        canonical_concept=definition.canonical_concept,
        target_field=definition.target_field,
        normalized_value=None,
        normalized_unit=definition.normalized_unit.value,
        confidence=confidence,
    )