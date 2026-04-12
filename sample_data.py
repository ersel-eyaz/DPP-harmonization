# This module provides small example input data for the sandbox.
# It creates a minimal raw dataset based on the scoped DPP fields
# so the project can be tested before any real harmonization logic is implemented.

from dataset import RawDataset
from enums import EntityType
from schemas import RawObservation


EXAMPLE_RAW_DATASET = RawDataset(
    observations=[
        RawObservation(
            entity_type=EntityType.DPP_INSTANCE,
            entity_id="dpp-001",
            raw_label="operatingHRS",
            raw_value=120.0,
            raw_unit="h",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.DPP_INSTANCE,
            entity_id="dpp-001",
            raw_label="cleaningCount",
            raw_value=14.0,
            raw_unit="count",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.DPP_INSTANCE,
            entity_id="dpp-001",
            raw_label="chalkCount",
            raw_value=3.0,
            raw_unit="count",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.DPP_INSTANCE,
            entity_id="dpp-001",
            raw_label="brewingCount",
            raw_value=560.0,
            raw_unit="count",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.MATERIAL_INSTANCE,
            entity_id="mat-001",
            raw_label="weightGRM",
            raw_value=540.0,
            raw_unit="g",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.MATERIAL_INSTANCE,
            entity_id="mat-001",
            raw_label="percentRecycled",
            raw_value=35.0,
            raw_unit="%",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.MATERIAL_INSTANCE,
            entity_id="mat-001",
            raw_label="purityLevel",
            raw_value=92.5,
            raw_unit="%",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.TRANSPORT_STEP,
            entity_id="transport-001",
            raw_label="distanceKM",
            raw_value=85.0,
            raw_unit="km",
            source_system="prototype_extract",
            source_file="sample",
        ),
        RawObservation(
            entity_type=EntityType.GHG_EMISSION_RECORD,
            entity_id="ghg-001",
            raw_label="emissions_kg_co2e",
            raw_value=12.4,
            raw_unit="kg_co2e",
            source_system="prototype_extract",
            source_file="sample",
        ),
    ]
)