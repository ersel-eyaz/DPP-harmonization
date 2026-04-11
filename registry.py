# Canonical registry built automatically from source model field metadata.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from enums import CanonicalConcept, EntityType, NormalizedUnit
from models import SOURCE_MODELS


class CanonicalFieldDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    canonical_concept: CanonicalConcept
    target_field: str
    normalized_unit: NormalizedUnit
    entity_type: EntityType
    description: str
    allowed_raw_labels: tuple[str, ...] = Field(default_factory=tuple)
    source_model: str
    source_field: str


def _build_definition_from_metadata(
    *,
    model_name: str,
    field_name: str,
    metadata: dict[str, Any],
) -> CanonicalFieldDefinition:
    return CanonicalFieldDefinition(
        canonical_concept=CanonicalConcept(metadata["canonical_concept"]),
        target_field=metadata["target_field"],
        normalized_unit=NormalizedUnit(metadata["normalized_unit"]),
        entity_type=EntityType(metadata["entity_type"]),
        description=metadata["description"],
        allowed_raw_labels=tuple(metadata["aliases"]),
        source_model=model_name,
        source_field=field_name,
    )


def build_canonical_field_registry() -> dict[CanonicalConcept, tuple[CanonicalFieldDefinition, ...]]:
    """
    Build a registry that allows multiple field definitions per canonical concept.

    This is required for many-to-one harmonization scenarios, where several
    different raw fields map to the same canonical concept.
    """
    grouped: dict[CanonicalConcept, list[CanonicalFieldDefinition]] = {}

    for model in SOURCE_MODELS:
        model_name = model.__name__

        for field_name, model_field in model.model_fields.items():
            extra = model_field.json_schema_extra or {}
            harmonization = extra.get("harmonization")

            if not harmonization:
                continue

            definition = _build_definition_from_metadata(
                model_name=model_name,
                field_name=field_name,
                metadata=harmonization,
            )

            concept = definition.canonical_concept
            grouped.setdefault(concept, []).append(definition)

    return {
        concept: tuple(definitions)
        for concept, definitions in grouped.items()
    }


def build_flat_field_definitions() -> tuple[CanonicalFieldDefinition, ...]:
    """
    Flatten the grouped registry into a single tuple of field definitions.

    This is useful for modules that need to iterate over every individual
    mapping candidate, such as similarity-based ranking or label indexing.
    """
    flat_definitions: list[CanonicalFieldDefinition] = []

    for definitions in CANONICAL_FIELD_REGISTRY.values():
        flat_definitions.extend(definitions)

    return tuple(flat_definitions)


CANONICAL_FIELD_REGISTRY = build_canonical_field_registry()
FLAT_FIELD_DEFINITIONS = build_flat_field_definitions()