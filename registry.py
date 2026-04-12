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


def build_canonical_field_registry() -> dict[CanonicalConcept, CanonicalFieldDefinition]:
    registry: dict[CanonicalConcept, CanonicalFieldDefinition] = {}

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

            if concept in registry:
                raise ValueError(
                    f"Duplicate canonical concept '{concept.value}' found in "
                    f"{model_name}.{field_name} and "
                    f"{registry[concept].source_model}.{registry[concept].source_field}"
                )

            registry[concept] = definition

    return registry


CANONICAL_FIELD_REGISTRY = build_canonical_field_registry()