from pydantic import BaseModel, Field, ConfigDict, field_validator

from enums import CanonicalConcept, EntityType


# This module defines the main data schemas used in the harmonization sandbox.
# It contains:
# - RawObservation for heterogeneous incoming inputs
# - HarmonizationRecord for normalized semantic outputs
#
# Raw observations intentionally preserve lightweight contextual metadata
# such as source node type, source path, and neighboring labels. This allows
# later harmonization stages to use more than isolated field names when
# resolving semantic meaning.


class HarmonizationRecord(BaseModel):
    raw_label: str = Field(..., min_length=1)
    raw_value: float | int | str | None = Field(default=None)
    canonical_concept: CanonicalConcept
    target_field: str = Field(..., min_length=1)
    normalized_value: float | int | str | None = Field(default=None)
    normalized_unit: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)


class RawObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: EntityType
    entity_id: str | None = None
    raw_label: str = Field(..., min_length=1)
    raw_value: float | int | str | None = None
    raw_unit: str | None = None
    source_system: str | None = None
    source_file: str | None = None

    # Lightweight contextual metadata captured during ingestion.
    source_node_type: str | None = None
    source_path: str | None = None
    neighbor_labels: list[str] = Field(default_factory=list)

    @field_validator("raw_label")
    @classmethod
    def strip_raw_label(cls, value: str) -> str:
        return value.strip()

    @field_validator("raw_unit")
    @classmethod
    def strip_raw_unit(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("source_system")
    @classmethod
    def strip_source_system(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("source_file")
    @classmethod
    def strip_source_file(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("source_node_type")
    @classmethod
    def strip_source_node_type(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("source_path")
    @classmethod
    def strip_source_path(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("neighbor_labels")
    @classmethod
    def normalize_neighbor_labels(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []

        for value in values:
            stripped = value.strip()
            if stripped:
                normalized.append(stripped)

        return normalized