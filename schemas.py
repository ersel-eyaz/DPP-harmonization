# This module defines the main data schemas used in the sandbox.
# It includes the raw observation format for incoming heterogeneous inputs
# and the harmonization output format for normalized semantic records.
# At this stage, the file only defines the structures, not the harmonization logic itself.

from pydantic import BaseModel, Field, ConfigDict, field_validator

from enums import CanonicalConcept, EntityType


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

    @field_validator("raw_label")
    @classmethod
    def strip_raw_label(cls, value: str) -> str:
        return value.strip()

    @field_validator("raw_unit")
    @classmethod
    def strip_raw_unit(cls, value: str | None) -> str | None:
        return value.strip() if value else value