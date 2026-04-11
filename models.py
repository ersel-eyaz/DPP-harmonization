# Source prototype models enriched with harmonization metadata.
# Each relevant field carries semantic information that can later be used
# to build the canonical registry automatically.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from enums import CanonicalConcept, EntityType, NormalizedUnit


def semantic_field(
    *,
    default: Any,
    canonical_concept: CanonicalConcept,
    target_field: str,
    normalized_unit: NormalizedUnit,
    entity_type: EntityType,
    aliases: list[str],
    description: str,
    **field_kwargs: Any,
) -> Any:
    """
    Helper for defining a Pydantic field with harmonization metadata.
    """
    return Field(
        default=default,
        json_schema_extra={
            "harmonization": {
                "canonical_concept": canonical_concept.value,
                "target_field": target_field,
                "normalized_unit": normalized_unit.value,
                "entity_type": entity_type.value,
                "aliases": aliases,
                "description": description,
            }
        },
        **field_kwargs,
    )


class DPPInstance(BaseModel):
    id: str | None = Field(default=None)

    cleaningCount: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.CLEANING_COUNT,
        target_field="cleaning_count",
        normalized_unit=NormalizedUnit.COUNT,
        entity_type=EntityType.DPP_INSTANCE,
        aliases=["cleaningCount", "cleanings", "cleaning_cycles"],
        description="Number of cleaning events recorded for a product instance.",
    )

    chalkCount: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.DESCALING_COUNT,
        target_field="descaling_count",
        normalized_unit=NormalizedUnit.COUNT,
        entity_type=EntityType.DPP_INSTANCE,
        aliases=["chalkCount", "descalingCount", "descale_cycles"],
        description="Number of descaling events recorded for a product instance.",
    )

    brewingCount: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.BREWING_COUNT,
        target_field="brewing_count",
        normalized_unit=NormalizedUnit.COUNT,
        entity_type=EntityType.DPP_INSTANCE,
        aliases=["brewingCount", "brewCount", "brewing_cycles"],
        description="Number of brewing cycles recorded for a product instance.",
    )

    operatingHRS: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.OPERATING_HOURS,
        target_field="operating_hours",
        normalized_unit=NormalizedUnit.HOURS,
        entity_type=EntityType.DPP_INSTANCE,
        aliases=["operatingHRS", "operatingHours"],
        description="Cumulative operating time of a product instance.",
    )

    runtimeHours: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.OPERATING_HOURS,
        target_field="operating_hours",
        normalized_unit=NormalizedUnit.HOURS,
        entity_type=EntityType.DPP_INSTANCE,
        aliases=["runtimeHours", "runtime_hrs", "hoursRuntime"],
        description="Runtime of a product instance expressed in hours.",
    )

    operationTimeHRS: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.OPERATING_HOURS,
        target_field="operating_hours",
        normalized_unit=NormalizedUnit.HOURS,
        entity_type=EntityType.DPP_INSTANCE,
        aliases=["operationTimeHRS", "operationHours", "timeInOperation"],
        description="Operational time of a product instance expressed in hours.",
    )

    backupLink: str | None = Field(default=None)


class MaterialInstance(BaseModel):
    batchNumber: str | None = Field(default=None)

    weightGRM: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.WEIGHT,
        target_field="weight",
        normalized_unit=NormalizedUnit.GRAM,
        entity_type=EntityType.MATERIAL_INSTANCE,
        aliases=["weightGRM", "weight_g", "massGram"],
        description="Mass of a material instance expressed in grams.",
    )

    weightKG: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.WEIGHT,
        target_field="weight",
        normalized_unit=NormalizedUnit.GRAM,
        entity_type=EntityType.MATERIAL_INSTANCE,
        aliases=["weightKG", "weight_kg", "massKilogram"],
        description="Mass of a material instance expressed in kilograms.",
    )

    percentRecycled: float = semantic_field(
        default=0.0,
        ge=0.0,
        le=100.0,
        canonical_concept=CanonicalConcept.RECYCLED_CONTENT,
        target_field="recycled_content",
        normalized_unit=NormalizedUnit.PERCENT,
        entity_type=EntityType.MATERIAL_INSTANCE,
        aliases=["percentRecycled", "recycledPercent", "recycled_content_pct"],
        description="Share of recycled material content expressed as a percentage.",
    )

    recycledRatio: float = semantic_field(
        default=0.0,
        ge=0.0,
        le=1.0,
        canonical_concept=CanonicalConcept.RECYCLED_CONTENT,
        target_field="recycled_content",
        normalized_unit=NormalizedUnit.PERCENT,
        entity_type=EntityType.MATERIAL_INSTANCE,
        aliases=["recycledRatio", "recycled_fraction", "ratioRecycled"],
        description="Share of recycled material content expressed as a ratio.",
    )

    purityLevel: float = semantic_field(
        default=0.0,
        ge=0.0,
        le=100.0,
        canonical_concept=CanonicalConcept.PURITY_LEVEL,
        target_field="purity_level",
        normalized_unit=NormalizedUnit.PERCENT,
        entity_type=EntityType.MATERIAL_INSTANCE,
        aliases=["purityLevel", "purity", "purity_pct"],
        description="Purity level of the material instance.",
    )


class TransportStep(BaseModel):
    distanceKM: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.TRANSPORT_DISTANCE,
        target_field="transport_distance",
        normalized_unit=NormalizedUnit.KILOMETER,
        entity_type=EntityType.TRANSPORT_STEP,
        aliases=["distanceKM", "distance_km", "transportDistance"],
        description="Distance covered by a transport step expressed in kilometers.",
    )

    routeLengthM: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.TRANSPORT_DISTANCE,
        target_field="transport_distance",
        normalized_unit=NormalizedUnit.KILOMETER,
        entity_type=EntityType.TRANSPORT_STEP,
        aliases=["routeLengthM", "distance_m", "routeMeters"],
        description="Distance covered by a transport step expressed in meters.",
    )


class GHGEmissionRecord(BaseModel):
    emissions_kg_co2e: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.GHG_EMISSIONS,
        target_field="ghg_emissions",
        normalized_unit=NormalizedUnit.KILOGRAM_CO2E,
        entity_type=EntityType.GHG_EMISSION_RECORD,
        aliases=["emissions_kg_co2e", "co2e", "ghgEmissions"],
        description="Greenhouse gas emissions expressed in kg CO2e.",
    )

    emissions_g_co2e: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.GHG_EMISSIONS,
        target_field="ghg_emissions",
        normalized_unit=NormalizedUnit.KILOGRAM_CO2E,
        entity_type=EntityType.GHG_EMISSION_RECORD,
        aliases=["emissions_g_co2e", "ghg_g_co2e", "co2e_grams"],
        description="Greenhouse gas emissions expressed in grams of CO2e.",
    )


class PartStatic(BaseModel):
    id: str | None = Field(default=None)

    weightGRM: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.WEIGHT,
        target_field="weight",
        normalized_unit=NormalizedUnit.GRAM,
        entity_type=EntityType.PART_STATIC,
        aliases=["weightGRM", "partWeightGRM", "staticWeightGram"],
        description="Static part weight expressed in grams.",
    )


class PartInstance(BaseModel):
    id: str | None = Field(default=None)

    weightKG: float = semantic_field(
        default=0.0,
        ge=0.0,
        canonical_concept=CanonicalConcept.WEIGHT,
        target_field="weight",
        normalized_unit=NormalizedUnit.GRAM,
        entity_type=EntityType.PART_INSTANCE,
        aliases=["weightKG", "partWeightKG", "instanceWeightKilogram"],
        description="Instance-specific part weight expressed in kilograms.",
    )


SOURCE_MODELS = (
    DPPInstance,
    MaterialInstance,
    TransportStep,
    GHGEmissionRecord,
    PartStatic,
    PartInstance,
)