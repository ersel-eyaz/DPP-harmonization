# This module defines the controlled vocabularies used in the DPP harmonization sandbox.
# It establishes the canonical concepts, normalized target units, and entity types
# required for a consistent semantic representation of the scoped data fields.
# By centralizing these definitions, later modules can avoid string inconsistency
# and rely on a stable shared vocabulary.

from enum import Enum


class CanonicalConcept(str, Enum):
    OPERATING_HOURS = "operating_hours"
    CLEANING_COUNT = "cleaning_count"
    DESCALING_COUNT = "descaling_count"
    BREWING_COUNT = "brewing_count"
    WEIGHT = "weight"
    RECYCLED_CONTENT = "recycled_content"
    PURITY_LEVEL = "purity_level"
    TRANSPORT_DISTANCE = "transport_distance"
    GHG_EMISSIONS = "ghg_emissions"


class NormalizedUnit(str, Enum):
    HOURS = "h"
    COUNT = "count"
    GRAM = "g"
    PERCENT = "%"
    KILOMETER = "km"
    KILOGRAM_CO2E = "kg_co2e"


class EntityType(str, Enum):
    DPP_INSTANCE = "DPPInstance"
    MATERIAL_INSTANCE = "MaterialInstance"
    TRANSPORT_STEP = "TransportStep"
    GHG_EMISSION_RECORD = "GHGEmissionRecord"
    PART_STATIC = "PartStatic"