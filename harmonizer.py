# Semantic harmonization logic for the DPP sandbox.
# It maps raw observations to canonical concepts, normalizes units and values,
# assigns a confidence score, and returns structured harmonization results.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataset import HarmonizedDataset
from enums import CanonicalConcept, EntityType, NormalizedUnit
from registry import CANONICAL_FIELD_REGISTRY, CanonicalFieldDefinition
from schemas import HarmonizationRecord, RawObservation


class HarmonizationError(ValueError):
    """Base error for harmonization failures."""


class LabelMappingError(HarmonizationError):
    """Raised when no canonical mapping can be found for a raw label."""


class UnitNormalizationError(HarmonizationError):
    """Raised when a raw unit cannot be normalized or converted."""


class ValueNormalizationError(HarmonizationError):
    """Raised when a raw value cannot be normalized."""


@dataclass(slots=True)
class UnmappedObservation:
    observation: RawObservation
    reason: str


@dataclass(slots=True)
class HarmonizationBatchResult:
    dataset: HarmonizedDataset = field(default_factory=HarmonizedDataset)
    unmapped: list[UnmappedObservation] = field(default_factory=list)


class DataHarmonizer:
    """
    Harmonizes raw observations into canonical semantic records.

    Current behavior:
    - label matching via registry aliases
    - entity-aware mapping
    - basic unit normalization and conversion
    - confidence scoring based on mapping/directness
    """

    def __init__(self) -> None:
        self._label_index = self._build_label_index()

    def harmonize_observation(self, observation: RawObservation) -> HarmonizationRecord:
        definition, label_confidence = self._resolve_definition(
            entity_type=observation.entity_type,
            raw_label=observation.raw_label,
        )

        normalized_value, unit_confidence = self._normalize_value_and_unit(
            raw_value=observation.raw_value,
            raw_unit=observation.raw_unit,
            concept=definition.canonical_concept,
            target_unit=definition.normalized_unit,
        )

        confidence = self._combine_confidences(label_confidence, unit_confidence)

        return HarmonizationRecord(
            raw_label=observation.raw_label,
            raw_value=observation.raw_value,
            canonical_concept=definition.canonical_concept,
            target_field=definition.target_field,
            normalized_value=normalized_value,
            normalized_unit=definition.normalized_unit.value,
            confidence=confidence,
        )

    def harmonize_dataset(self, observations: list[RawObservation]) -> HarmonizationBatchResult:
        result = HarmonizationBatchResult()

        for observation in observations:
            try:
                record = self.harmonize_observation(observation)
                result.dataset.add(record)
            except HarmonizationError as exc:
                result.unmapped.append(
                    UnmappedObservation(
                        observation=observation,
                        reason=str(exc),
                    )
                )

        return result

    def harmonize_dataset_container(self, raw_dataset: Any) -> HarmonizationBatchResult:
        """
        Accepts a RawDataset-like object with an `observations` attribute.
        """
        observations = getattr(raw_dataset, "observations", None)
        if observations is None or not isinstance(observations, list):
            raise TypeError("Expected an object with an `observations: list[RawObservation]` attribute.")
        return self.harmonize_dataset(observations)

    def _build_label_index(self) -> dict[tuple[EntityType, str], CanonicalFieldDefinition]:
        index: dict[tuple[EntityType, str], CanonicalFieldDefinition] = {}

        for definition in CANONICAL_FIELD_REGISTRY.values():
            for raw_label in definition.allowed_raw_labels:
                key = (definition.entity_type, self._normalize_text(raw_label))
                index[key] = definition

        return index

    def _resolve_definition(
        self,
        entity_type: EntityType,
        raw_label: str,
    ) -> tuple[CanonicalFieldDefinition, float]:
        normalized_label = self._normalize_text(raw_label)
        key = (entity_type, normalized_label)

        definition = self._label_index.get(key)
        if definition is None:
            raise LabelMappingError(
                f"No canonical mapping found for raw label '{raw_label}' "
                f"under entity type '{entity_type.value}'."
            )

        if raw_label in definition.allowed_raw_labels:
            label_confidence = 1.0
        else:
            label_confidence = 0.92

        return definition, label_confidence

    def _normalize_value_and_unit(
        self,
        raw_value: float | int | str | None,
        raw_unit: str | None,
        concept: CanonicalConcept,
        target_unit: NormalizedUnit,
    ) -> tuple[float | int | str | None, float]:
        if raw_value is None:
            return None, 0.7

        if isinstance(raw_value, str):
            raw_value = raw_value.strip()
            if raw_value == "":
                return None, 0.7

        # Count-like concepts can tolerate missing units better.
        if concept in {
            CanonicalConcept.CLEANING_COUNT,
            CanonicalConcept.DESCALING_COUNT,
            CanonicalConcept.BREWING_COUNT,
        }:
            numeric_value = self._coerce_numeric(raw_value)
            normalized_unit = self._normalize_unit_token(raw_unit) if raw_unit else target_unit.value

            if normalized_unit in {target_unit.value, "cycle", "cycles", "event", "events"}:
                return numeric_value, 0.98 if raw_unit else 0.9

            raise UnitNormalizationError(
                f"Unsupported unit '{raw_unit}' for count-like concept '{concept.value}'."
            )

        numeric_value = self._coerce_numeric(raw_value)

        from_unit = self._normalize_unit_token(raw_unit)
        to_unit = target_unit.value

        if from_unit == to_unit:
            return numeric_value, 1.0

        converted_value = self._convert_unit_value(
            value=numeric_value,
            from_unit=from_unit,
            to_unit=to_unit,
            concept=concept,
        )
        return converted_value, 0.9

    def _coerce_numeric(self, value: float | int | str) -> float:
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            candidate = value.strip().replace(",", ".")
            try:
                return float(candidate)
            except ValueError as exc:
                raise ValueNormalizationError(f"Cannot parse numeric value from '{value}'.") from exc

        raise ValueNormalizationError(f"Unsupported raw value type: {type(value).__name__}")

    def _normalize_unit_token(self, raw_unit: str | None) -> str:
        if raw_unit is None:
            raise UnitNormalizationError("Missing raw unit for unit-based concept.")

        token = raw_unit.strip().lower()

        unit_aliases = {
            # hours
            "h": "h",
            "hr": "h",
            "hrs": "h",
            "hour": "h",
            "hours": "h",
            # count
            "count": "count",
            "counts": "count",
            "cycle": "cycle",
            "cycles": "cycles",
            "event": "event",
            "events": "events",
            # grams / kilograms / milligrams
            "g": "g",
            "gr": "g",
            "gram": "g",
            "grams": "g",
            "kg": "kg",
            "kilogram": "kg",
            "kilograms": "kg",
            "mg": "mg",
            "milligram": "mg",
            "milligrams": "mg",
            # percent / ratio
            "%": "%",
            "pct": "%",
            "percent": "%",
            "percentage": "%",
            "ratio": "ratio",
            "fraction": "ratio",
            # distance
            "km": "km",
            "kilometer": "km",
            "kilometers": "km",
            "kilometre": "km",
            "kilometres": "km",
            "m": "m",
            "meter": "m",
            "meters": "m",
            "metre": "m",
            "metres": "m",
            # emissions
            "kgco2e": "kg_co2e",
            "kg_co2e": "kg_co2e",
            "kgco2eq": "kg_co2e",
            "kgco2equivalent": "kg_co2e",
            "kgco2eqv": "kg_co2e",
            "gco2e": "g_co2e",
            "g_co2e": "g_co2e",
        }

        normalized = unit_aliases.get(token)
        if normalized is None:
            raise UnitNormalizationError(f"Unknown or unsupported raw unit '{raw_unit}'.")
        return normalized

    def _convert_unit_value(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        concept: CanonicalConcept,
    ) -> float:
        if from_unit == to_unit:
            return value

        # weight
        if concept == CanonicalConcept.WEIGHT and to_unit == NormalizedUnit.GRAM.value:
            if from_unit == "kg":
                return value * 1000.0
            if from_unit == "mg":
                return value / 1000.0

        # percentages
        if concept in {CanonicalConcept.RECYCLED_CONTENT, CanonicalConcept.PURITY_LEVEL} and to_unit == "%":
            if from_unit == "ratio":
                return value * 100.0

        # transport distance
        if concept == CanonicalConcept.TRANSPORT_DISTANCE and to_unit == NormalizedUnit.KILOMETER.value:
            if from_unit == "m":
                return value / 1000.0

        # ghg emissions
        if concept == CanonicalConcept.GHG_EMISSIONS and to_unit == NormalizedUnit.KILOGRAM_CO2E.value:
            if from_unit == "g_co2e":
                return value / 1000.0

        raise UnitNormalizationError(
            f"Cannot convert from '{from_unit}' to '{to_unit}' for concept '{concept.value}'."
        )

    def _combine_confidences(self, label_confidence: float, unit_confidence: float) -> float:
        confidence = (label_confidence * 0.65) + (unit_confidence * 0.35)
        return round(min(max(confidence, 0.0), 1.0), 3)

    @staticmethod
    def _normalize_text(value: str) -> str:
        return "".join(ch for ch in value.strip().lower() if ch.isalnum())


def harmonize_observations(observations: list[RawObservation]) -> HarmonizationBatchResult:
    harmonizer = DataHarmonizer()
    return harmonizer.harmonize_dataset(observations)