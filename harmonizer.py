from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataset import HarmonizedDataset
from enums import CanonicalConcept, EntityType, NormalizedUnit
from registry import FLAT_FIELD_DEFINITIONS, CanonicalFieldDefinition
from schemas import HarmonizationRecord, RawObservation


# Rule-based semantic harmonization logic for the DPP sandbox.
# This module is the main harmonization resolver.
#
# Resolution strategy:
# - filter by structured constraints first (especially entity type)
# - resolve labels deterministically through source fields and aliases
# - normalize values and units
# - return structured harmonization records with a transparent confidence score
#
# Similarity-based ranking is intentionally not the main decision mechanism here.
# It can still be used separately as a fallback suggestion tool for unknown labels.


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
    Deterministic rule-based harmonizer for raw observations.

    Current behavior:
    - entity-aware label resolution via registry metadata
    - exact/alias-based canonical mapping
    - unit normalization and conversion
    - basic confidence scoring based on how direct the mapping was
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
        Accept a RawDataset-like object with an `observations` attribute.
        """
        observations = getattr(raw_dataset, "observations", None)
        if observations is None or not isinstance(observations, list):
            raise TypeError("Expected an object with an `observations: list[RawObservation]` attribute.")
        return self.harmonize_dataset(observations)

    def _build_label_index(self) -> dict[tuple[EntityType, str], list[CanonicalFieldDefinition]]:
        """
        Build an entity-aware lookup index.

        The same raw label may exist across multiple entities, so entity type
        is part of the key and acts as a hard structural constraint.
        """
        index: dict[tuple[EntityType, str], list[CanonicalFieldDefinition]] = {}

        for definition in FLAT_FIELD_DEFINITIONS:
            labels = {definition.source_field, *definition.allowed_raw_labels}

            for raw_label in labels:
                key = (definition.entity_type, self._normalize_text(raw_label))
                index.setdefault(key, []).append(definition)

        return index

    def _resolve_definition(
        self,
        entity_type: EntityType,
        raw_label: str,
    ) -> tuple[CanonicalFieldDefinition, float]:
        """
        Resolve a canonical field definition deterministically.

        Resolution is restricted to the given entity type. This avoids treating
        entity type as a soft signal and instead uses it as a hard filter.
        """
        normalized_label = self._normalize_text(raw_label)
        key = (entity_type, normalized_label)

        candidates = self._label_index.get(key)
        if not candidates:
            raise LabelMappingError(
                f"No canonical mapping found for raw label '{raw_label}' "
                f"under entity type '{entity_type.value}'."
            )

        if len(candidates) > 1:
            raise LabelMappingError(
                f"Ambiguous canonical mapping for raw label '{raw_label}' "
                f"under entity type '{entity_type.value}'."
            )

        definition = candidates[0]

        exact_source_field_match = raw_label == definition.source_field
        exact_alias_match = raw_label in definition.allowed_raw_labels
        normalized_source_field_match = normalized_label == self._normalize_text(definition.source_field)
        normalized_alias_match = any(
            normalized_label == self._normalize_text(alias)
            for alias in definition.allowed_raw_labels
        )

        if exact_source_field_match or exact_alias_match:
            label_confidence = 1.0
        elif normalized_source_field_match or normalized_alias_match:
            label_confidence = 0.95
        else:
            label_confidence = 0.9

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
            # percent
            "%": "%",
            "pct": "%",
            "percent": "%",
            "percentage": "%",
            # distance
            "km": "km",
            "kilometer": "km",
            "kilometers": "km",
            # ghg emissions
            "kg_co2e": "kg_co2e",
            "kgco2e": "kg_co2e",
            "kg-co2e": "kg_co2e",
            "kg co2e": "kg_co2e",
        }

        try:
            return unit_aliases[token]
        except KeyError as exc:
            raise UnitNormalizationError(f"Unsupported raw unit '{raw_unit}'.") from exc

    def _convert_unit_value(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        concept: CanonicalConcept,
    ) -> float:
        if from_unit == to_unit:
            return value

        if concept == CanonicalConcept.WEIGHT:
            if from_unit == "kg" and to_unit == "g":
                return value * 1000.0
            if from_unit == "mg" and to_unit == "g":
                return value / 1000.0

        raise UnitNormalizationError(
            f"Cannot convert unit '{from_unit}' to '{to_unit}' "
            f"for concept '{concept.value}'."
        )

    def _combine_confidences(self, label_confidence: float, unit_confidence: float) -> float:
        """
        Combine label and normalization confidence into a single score.
        """
        score = 0.7 * label_confidence + 0.3 * unit_confidence
        return round(score, 4)

    def _normalize_text(self, text: str) -> str:
        """
        Normalize labels for deterministic lookup.

        This is intentionally lightweight:
        - strip whitespace
        - lowercase
        - collapse separators commonly seen in field names
        """
        return (
            text.strip()
            .lower()
            .replace("-", "")
            .replace("_", "")
            .replace(" ", "")
        )