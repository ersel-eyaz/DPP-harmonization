from __future__ import annotations

from pydantic import BaseModel, Field

from enums import CanonicalConcept, EntityType
from schemas import RawObservation


class EvaluationCase(BaseModel):
    raw_label: str = Field(..., min_length=1)
    entity_type: EntityType
    raw_unit: str | None = None
    raw_value: float | int | str | None = None

    # None means the observation is expected to stay unmapped.
    expected_canonical_concept: CanonicalConcept | None = None

    # Allowed values: easy, medium, hard, negative
    difficulty: str = Field(..., min_length=1)

    # Optional note for why this case belongs to a given difficulty level.
    note: str | None = None

    def to_raw_observation(self) -> RawObservation:
        return RawObservation(
            entity_type=self.entity_type,
            entity_id="eval-case",
            raw_label=self.raw_label,
            raw_value=self.raw_value,
            raw_unit=self.raw_unit,
            source_system="evaluation_dataset",
            source_file="evaluation_cases.py",
        )


EXAMPLE_EVALUATION_CASES = [
    # -------------------------
    # EASY (10)
    # -------------------------
    EvaluationCase(
        raw_label="operatingHRS",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="h",
        raw_value=120.0,
        expected_canonical_concept=CanonicalConcept.OPERATING_HOURS,
        difficulty="easy",
        note="Exact source field.",
    ),
    EvaluationCase(
        raw_label="operatingHours",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="hours",
        raw_value=120.0,
        expected_canonical_concept=CanonicalConcept.OPERATING_HOURS,
        difficulty="easy",
        note="Direct allowed alias.",
    ),
    EvaluationCase(
        raw_label="cleaning_cycles",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="count",
        raw_value=14.0,
        expected_canonical_concept=CanonicalConcept.CLEANING_COUNT,
        difficulty="easy",
        note="Direct allowed alias.",
    ),
    EvaluationCase(
        raw_label="descalingCount",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="count",
        raw_value=3.0,
        expected_canonical_concept=CanonicalConcept.DESCALING_COUNT,
        difficulty="easy",
        note="Direct allowed alias.",
    ),
    EvaluationCase(
        raw_label="brewCount",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="count",
        raw_value=560.0,
        expected_canonical_concept=CanonicalConcept.BREWING_COUNT,
        difficulty="easy",
        note="Direct allowed alias.",
    ),
    EvaluationCase(
        raw_label="percentRecycled",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="%",
        raw_value=35.0,
        expected_canonical_concept=CanonicalConcept.RECYCLED_CONTENT,
        difficulty="easy",
        note="Exact source field.",
    ),
    EvaluationCase(
        raw_label="purity_pct",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="%",
        raw_value=92.5,
        expected_canonical_concept=CanonicalConcept.PURITY_LEVEL,
        difficulty="easy",
        note="Direct allowed alias.",
    ),
    EvaluationCase(
        raw_label="componentWeightGRM",
        entity_type=EntityType.PART_STATIC,
        raw_unit="g",
        raw_value=1800.0,
        expected_canonical_concept=CanonicalConcept.WEIGHT,
        difficulty="easy",
        note="Direct allowed alias.",
    ),
    EvaluationCase(
        raw_label="transportDistance",
        entity_type=EntityType.TRANSPORT_STEP,
        raw_unit="km",
        raw_value=85.0,
        expected_canonical_concept=CanonicalConcept.TRANSPORT_DISTANCE,
        difficulty="easy",
        note="Direct allowed alias.",
    ),
    EvaluationCase(
        raw_label="ghgEmissions",
        entity_type=EntityType.GHG_EMISSION_RECORD,
        raw_unit="kg_co2e",
        raw_value=12.4,
        expected_canonical_concept=CanonicalConcept.GHG_EMISSIONS,
        difficulty="easy",
        note="Direct allowed alias.",
    ),

    # -------------------------
    # MEDIUM (10)
    # -------------------------
    EvaluationCase(
        raw_label="runtime_hours_total",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="hours",
        raw_value=120.0,
        expected_canonical_concept=CanonicalConcept.OPERATING_HOURS,
        difficulty="medium",
        note="Extra token plus separator variation.",
    ),
    EvaluationCase(
        raw_label="cleaning_events_total",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="events",
        raw_value=14.0,
        expected_canonical_concept=CanonicalConcept.CLEANING_COUNT,
        difficulty="medium",
        note="Event wording instead of count wording.",
    ),
    EvaluationCase(
        raw_label="descale_event_count",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="count",
        raw_value=3.0,
        expected_canonical_concept=CanonicalConcept.DESCALING_COUNT,
        difficulty="medium",
        note="Descale wording with extra token.",
    ),
    EvaluationCase(
        raw_label="brew_cycle_total",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="cycles",
        raw_value=560.0,
        expected_canonical_concept=CanonicalConcept.BREWING_COUNT,
        difficulty="medium",
        note="Cycle wording plus total suffix.",
    ),
    EvaluationCase(
        raw_label="material_mass_grams",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="gram",
        raw_value=540.0,
        expected_canonical_concept=CanonicalConcept.WEIGHT,
        difficulty="medium",
        note="Mass wording instead of weight.",
    ),
    EvaluationCase(
        raw_label="recycled_material_share",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="percent",
        raw_value=35.0,
        expected_canonical_concept=CanonicalConcept.RECYCLED_CONTENT,
        difficulty="medium",
        note="Share wording instead of percent label.",
    ),
    EvaluationCase(
        raw_label="material_purity_percentage",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="percentage",
        raw_value=92.5,
        expected_canonical_concept=CanonicalConcept.PURITY_LEVEL,
        difficulty="medium",
        note="Expanded wording around purity.",
    ),
    EvaluationCase(
        raw_label="part_mass_grams",
        entity_type=EntityType.PART_STATIC,
        raw_unit="grams",
        raw_value=1800.0,
        expected_canonical_concept=CanonicalConcept.WEIGHT,
        difficulty="medium",
        note="Part weight expressed through mass.",
    ),
    EvaluationCase(
        raw_label="travel_distance_km",
        entity_type=EntityType.TRANSPORT_STEP,
        raw_unit="kilometers",
        raw_value=91.0,
        expected_canonical_concept=CanonicalConcept.TRANSPORT_DISTANCE,
        difficulty="medium",
        note="Travel wording instead of transport.",
    ),
    EvaluationCase(
        raw_label="carbon_emissions_kg_co2e",
        entity_type=EntityType.GHG_EMISSION_RECORD,
        raw_unit="kg co2e",
        raw_value=13.1,
        expected_canonical_concept=CanonicalConcept.GHG_EMISSIONS,
        difficulty="medium",
        note="Carbon wording instead of ghg label.",
    ),

    # -------------------------
    # HARD (10)
    # -------------------------
    EvaluationCase(
        raw_label="machine_usage_duration",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="hr",
        raw_value=120.0,
        expected_canonical_concept=CanonicalConcept.OPERATING_HOURS,
        difficulty="hard",
        note="Low lexical overlap with operating hours.",
    ),
    EvaluationCase(
        raw_label="cleaning_runs_completed",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="events",
        raw_value=14.0,
        expected_canonical_concept=CanonicalConcept.CLEANING_COUNT,
        difficulty="hard",
        note="Paraphrased cleaning count.",
    ),
    EvaluationCase(
        raw_label="lime_removal_operations",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="count",
        raw_value=3.0,
        expected_canonical_concept=CanonicalConcept.DESCALING_COUNT,
        difficulty="hard",
        note="Paraphrased descaling terminology.",
    ),
    EvaluationCase(
        raw_label="coffee_preparation_cycles",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit="cycles",
        raw_value=560.0,
        expected_canonical_concept=CanonicalConcept.BREWING_COUNT,
        difficulty="hard",
        note="Paraphrased brewing count.",
    ),
    EvaluationCase(
        raw_label="material_load_value",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="g",
        raw_value=540.0,
        expected_canonical_concept=CanonicalConcept.WEIGHT,
        difficulty="hard",
        note="Weak lexical cue for weight.",
    ),
    EvaluationCase(
        raw_label="secondary_input_fraction",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="pct",
        raw_value=35.0,
        expected_canonical_concept=CanonicalConcept.RECYCLED_CONTENT,
        difficulty="hard",
        note="Paraphrased recycled content.",
    ),
    EvaluationCase(
        raw_label="refinement_grade_value",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit="percent",
        raw_value=92.5,
        expected_canonical_concept=CanonicalConcept.PURITY_LEVEL,
        difficulty="hard",
        note="Indirect purity wording.",
    ),
    EvaluationCase(
        raw_label="component_mass_total_value",
        entity_type=EntityType.PART_STATIC,
        raw_unit="g",
        raw_value=1800.0,
        expected_canonical_concept=CanonicalConcept.WEIGHT,
        difficulty="hard",
        note="Longer noisy variant for part weight.",
    ),
    EvaluationCase(
        raw_label="route_length_value",
        entity_type=EntityType.TRANSPORT_STEP,
        raw_unit="km",
        raw_value=91.0,
        expected_canonical_concept=CanonicalConcept.TRANSPORT_DISTANCE,
        difficulty="hard",
        note="Distance phrased via route length.",
    ),
    EvaluationCase(
        raw_label="climate_impact_output",
        entity_type=EntityType.GHG_EMISSION_RECORD,
        raw_unit="kg-co2e",
        raw_value=13.1,
        expected_canonical_concept=CanonicalConcept.GHG_EMISSIONS,
        difficulty="hard",
        note="Very indirect wording for emissions.",
    ),

    # -------------------------
    # NEGATIVE (5)
    # -------------------------
    EvaluationCase(
        raw_label="backupLink",
        entity_type=EntityType.DPP_INSTANCE,
        raw_unit=None,
        raw_value="https://example.org/dpp-backup/dpp-001",
        expected_canonical_concept=None,
        difficulty="negative",
        note="Out of scope field.",
    ),
    EvaluationCase(
        raw_label="manufacturer_name",
        entity_type=EntityType.PART_STATIC,
        raw_unit=None,
        raw_value="Acme Components",
        expected_canonical_concept=None,
        difficulty="negative",
        note="Out of scope metadata field.",
    ),
    EvaluationCase(
        raw_label="batchNumber",
        entity_type=EntityType.MATERIAL_INSTANCE,
        raw_unit=None,
        raw_value="batch-001",
        expected_canonical_concept=None,
        difficulty="negative",
        note="Identifier field, not a scoped canonical concept.",
    ),
    EvaluationCase(
        raw_label="transportMode",
        entity_type=EntityType.TRANSPORT_STEP,
        raw_unit=None,
        raw_value="road",
        expected_canonical_concept=None,
        difficulty="negative",
        note="Transport metadata, not transport distance.",
    ),
    EvaluationCase(
        raw_label="calculation_method",
        entity_type=EntityType.GHG_EMISSION_RECORD,
        raw_unit=None,
        raw_value="GHG Protocol",
        expected_canonical_concept=None,
        difficulty="negative",
        note="Method metadata, not emission value.",
    ),
]