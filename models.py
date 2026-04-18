from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# GHG enums
# ---------------------------------------------------------------------------


class GHGScope(str, Enum):
    SCOPE_1 = "Scope 1"
    SCOPE_2 = "Scope 2"
    SCOPE_3 = "Scope 3"


class Scope3Category(str, Enum):
    PURCHASED_GOODS_AND_SERVICES = "Purchased goods and services"
    CAPITAL_GOODS = "Capital goods"
    FUEL_AND_ENERGY_RELATED_ACTIVITIES = "Fuel- and energy-related activities not included in Scope 1 or 2"
    UPSTREAM_TRANSPORTATION_AND_DISTRIBUTION = "Upstream transportation and distribution"
    WASTE_GENERATED_IN_OPERATIONS = "Waste generated in operations"
    BUSINESS_TRAVEL = "Business travel"
    EMPLOYEE_COMMUTING = "Employee commuting"
    UPSTREAM_LEASED_ASSETS = "Upstream leased assets"
    DOWNSTREAM_TRANSPORTATION_AND_DISTRIBUTION = "Downstream transportation and distribution"
    PROCESSING_OF_SOLD_PRODUCTS = "Processing of sold products"
    USE_OF_SOLD_PRODUCTS = "Use of sold products"
    END_OF_LIFE_TREATMENT = "End-of-life treatment of sold products"
    DOWNSTREAM_LEASED_ASSETS = "Downstream leased assets"
    FRANCHISES = "Franchises"
    INVESTMENTS = "Investments"


class ActivityType(str, Enum):
    ELECTRICITY_CONSUMPTION = "electricity_consumption"
    DISTANCE_TRAVELED = "distance_traveled"
    MATERIAL_PURCHASE = "material_purchase"
    WATER_USAGE = "water_usage"
    HEAT_USAGE = "heat_usage"
    WASTE_TREATMENT = "waste_treatment"
    FUEL_CONSUMPTION = "fuel_consumption"


class UnitCode(str, Enum):
    KWH = "kWh"
    KM = "km"
    KG = "kg"
    LTR = "ltr"
    M3 = "m3"
    TONNE = "t"
    PIECE = "unit"
    KG_CO2E_PER_KWH = "kgCO2e/kWh"
    KG_CO2E_PER_KG = "kgCO2e/kg"
    KG_CO2E_PER_KM = "kgCO2e/km"


# ---------------------------------------------------------------------------
# GHG models
# ---------------------------------------------------------------------------


class EmissionFactor(BaseModel):
    description: str | None = None
    value: float
    unit: UnitCode
    technology: Optional[str] = None

    @field_validator("value")
    @classmethod
    def _non_negative_value(cls, v: float) -> float:
        if v < 0:
            raise ValueError("value must be non-negative")
        return float(v)


class ActivityData(BaseModel):
    activity_type: ActivityType
    quantity: float
    unit: UnitCode

    @field_validator("quantity")
    @classmethod
    def _non_negative_quantity(cls, v: float) -> float:
        if v < 0:
            raise ValueError("quantity must be non-negative")
        return float(v)


class GHGEmissionRecord(BaseModel):
    scope: GHGScope
    scope3_category: Optional[Scope3Category] = None
    activity: ActivityData
    emission_factor: EmissionFactor
    emissions_kg_co2e: float
    calculation_method: str
    provenance: Optional[str] = None

    @field_validator("emissions_kg_co2e")
    @classmethod
    def _non_negative_emissions(cls, v: float) -> float:
        if v < 0:
            raise ValueError("emissions_kg_co2e must be non-negative")
        return float(v)


# ---------------------------------------------------------------------------
# Process model
# ---------------------------------------------------------------------------


class ProcessStep(BaseModel):
    type_: str = Field(default="ProcessStep", alias="type")
    beginDate: Optional[datetime] = Field(default_factory=_utc_now)
    endDate: Optional[datetime] = Field(default_factory=_utc_now)
    ghgEmissionRecords: list[GHGEmissionRecord] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


# ---------------------------------------------------------------------------
# Material models
# ---------------------------------------------------------------------------


class MaterialStatic(BaseModel):
    id: str
    type_: str = Field(default="MaterialStatic", alias="type")

    hazardous: bool = False
    rareEarth: bool = False

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class MaterialInstance(BaseModel):
    id: str
    type_: str = Field(default="MaterialInstance", alias="type")

    materialStaticLink: MaterialStatic
    weightGRM: float
    percentRecycled: float
    purityLevel: float

    @field_validator("weightGRM")
    @classmethod
    def _non_negative_weight(cls, v: float) -> float:
        if v < 0:
            raise ValueError("weightGRM must be non-negative")
        return float(v)

    @field_validator("percentRecycled")
    @classmethod
    def _percent_range(cls, v: float) -> float:
        if not 0 <= v <= 100:
            raise ValueError("percentRecycled must be between 0 and 100")
        return float(v)

    @field_validator("purityLevel")
    @classmethod
    def _non_negative_purity(cls, v: float) -> float:
        if v < 0:
            raise ValueError("purityLevel must be non-negative")
        return float(v)

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


# ---------------------------------------------------------------------------
# Part models
# ---------------------------------------------------------------------------


class PartStatic(BaseModel):
    id: str
    type_: str = Field(default="PartStatic", alias="type")

    weightGRM: float
    mtbfHRS: float

    @field_validator("weightGRM")
    @classmethod
    def _positive_weight(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("weightGRM must be positive")
        return float(v)

    @field_validator("mtbfHRS")
    @classmethod
    def _non_negative_mtbf(cls, v: float) -> float:
        if v < 0:
            raise ValueError("mtbfHRS must be non-negative")
        return float(v)

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class PartInstance(BaseModel):
    id: str
    type_: str = Field(default="PartInstance", alias="type")

    partStaticLink: PartStatic
    isModular: bool = Field(default=False)
    hasFailstate: bool = Field(default=False)

    compositeParts: list["PartInstance"] = Field(default_factory=list)
    compositeMaterials: list[MaterialInstance] = Field(default_factory=list)

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


# ---------------------------------------------------------------------------
# DPP model
# ---------------------------------------------------------------------------


class DPPInstance(BaseModel):
    id: str
    type_: str = Field(default="DPPInstance", alias="type")

    partInstanceLink: Optional[PartInstance] = None

    operatingHRS: float = 0.0
    cleaningCount: float = 0.0
    chalkCount: float = 0.0
    brewingCount: float = 0.0

    @field_validator("operatingHRS", "cleaningCount", "chalkCount", "brewingCount")
    @classmethod
    def _non_negative_counters(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Counters must be non-negative")
        return float(v)

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


# ---------------------------------------------------------------------------
# Forward refs
# ---------------------------------------------------------------------------

PartInstance.model_rebuild()
DPPInstance.model_rebuild()