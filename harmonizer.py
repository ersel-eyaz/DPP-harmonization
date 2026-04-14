from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataset import HarmonizedDataset
from enums import CanonicalConcept, EntityType, NormalizedUnit
from registry import FLAT_FIELD_DEFINITIONS, CanonicalFieldDefinition
from schemas import HarmonizationRecord, RawObservation
from similarity import (
    build_canonical_candidates,
    build_observation_query,
    rank_candidates,
)


# Rule-based semantic harmonization logic for the DPP sandbox.
# This module is the main harmonization resolver.
#
# Resolution strategy:
# - filter by structured constraints first (especially entity type)
# - resolve labels deterministically through source fields and aliases
# - use lightweight node context when available
# - if rule-based resolution fails, try similarity-based fallback
# - normalize values and units
# - return structured harmonization records with a transparent confidence score


class HarmonizationError(ValueError):
    """Base error for harmonization failures."""


class LabelMappingError(HarmonizationError):
    """Raised when no canonical mapping can be found."""


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

@dataclass(slots=True)
class ResolutionResult:
    definition: CanonicalFieldDefinition
    label_confidence: float
    resolution_method: str
    similarity_score: float | None = None


class DataHarmonizer:
    """
    Deterministic rule-based harmonizer for raw observations.

    Current behavior:
    - entity-aware label resolution via registry metadata
    - exact/alias-based canonical mapping
    - lightweight context-aware disambiguation
    - similarity-based fallback for unresolved labels
    - unit normalization and conversion
    - basic confidence scoring based on mapping directness and context support
    """

    def __init__(self, similarity_threshold: float = 0.55) -> None:
        self._label_index = self._build_label_index()
        self._similarity_threshold = similarity_threshold
        self._similarity_candidates = build_canonical_candidates()

    def harmonize_observation(self, observation: RawObservation) -> HarmonizationRecord:
        resolution = self._resolve_definition_with_fallback(observation)

        normalized_value, unit_confidence = self._normalize_value_and_unit(
            raw_value=observation.raw_value,
            raw_unit=observation.raw_unit,
            concept=resolution.definition.canonical_concept,
            target_unit=resolution.definition.normalized_unit,
        )

        confidence = self._combine_confidences(resolution.label_confidence, unit_confidence)

        return HarmonizationRecord(
            raw_label=observation.raw_label,
            raw_value=observation.raw_value,
            canonical_concept=resolution.definition.canonical_concept,
            target_field=resolution.definition.target_field,
            normalized_value=normalized_value,
            normalized_unit=resolution.definition.normalized_unit.value,
            confidence=confidence,
            resolution_method=resolution.resolution_method,
            matched_source_field=resolution.definition.source_field,
            matched_source_model=resolution.definition.source_model,
            label_confidence=resolution.label_confidence,
            unit_confidence=unit_confidence,
            similarity_score=resolution.similarity_score,
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
                existing = index.setdefault(key, [])

                if definition not in existing:
                    existing.append(definition)

        return index

    def _resolve_definition_with_fallback(
        self,
        observation: RawObservation,
    ) -> ResolutionResult:
        """
        Try deterministic resolution first. If it fails, use similarity-based fallback.
        """
        try:
            definition, label_confidence = self._resolve_definition(
                entity_type=observation.entity_type,
                raw_label=observation.raw_label,
                source_node_type=observation.source_node_type,
                neighbor_labels=observation.neighbor_labels,
            )
            return ResolutionResult(
                definition=definition,
                label_confidence=label_confidence,
                resolution_method="rule_based",
                similarity_score=None,
            )
        except LabelMappingError:
            definition, label_confidence, similarity_score = self._resolve_definition_with_similarity(observation)
            return ResolutionResult(
                definition=definition,
                label_confidence=label_confidence,
                resolution_method="similarity_fallback",
                similarity_score=similarity_score,
            )

    def _resolve_definition(
        self,
        entity_type: EntityType,
        raw_label: str,
        source_node_type: str | None = None,
        neighbor_labels: list[str] | None = None,
    ) -> tuple[CanonicalFieldDefinition, float]:
        """
        Resolve a canonical field definition deterministically.

        Resolution is restricted to the given entity type. If more than one
        candidate remains, lightweight node context is used as a tie-breaker.
        """
        normalized_label = self._normalize_text(raw_label)
        key = (entity_type, normalized_label)

        candidates = self._label_index.get(key)
        if not candidates:
            raise LabelMappingError(
                f"No canonical mapping found for raw label '{raw_label}' "
                f"under entity type '{entity_type.value}'."
            )

        if len(candidates) == 1:
            definition = candidates[0]
        else:
            definition = self._disambiguate_with_context(
                candidates=candidates,
                source_node_type=source_node_type,
                neighbor_labels=neighbor_labels or [],
                raw_label=raw_label,
                entity_type=entity_type,
            )

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

        context_bonus = self._context_confidence_bonus(
            definition=definition,
            source_node_type=source_node_type,
            neighbor_labels=neighbor_labels or [],
        )

        return definition, min(1.0, round(label_confidence + context_bonus, 4))

    def _resolve_definition_with_similarity(
        self,
        observation: RawObservation,
    ) -> tuple[CanonicalFieldDefinition, float, float]:
        """
        Fallback resolution using lexical similarity ranking.

        Similarity is restricted to the same entity type first. If nothing remains,
        all candidates are considered.
        """
        query = build_observation_query(observation)

        same_entity_candidates = [
            candidate
            for candidate in self._similarity_candidates
            if candidate.entity_type == observation.entity_type.value
        ]

        candidate_pool = same_entity_candidates if same_entity_candidates else self._similarity_candidates
        ranked = rank_candidates(query, candidate_pool)

        if not ranked:
            raise LabelMappingError(
                f"No canonical mapping found for raw label '{observation.raw_label}' "
                f"under entity type '{observation.entity_type.value}'."
            )

        top_match = ranked[0]

        if top_match.score < self._similarity_threshold:
            raise LabelMappingError(
                f"No sufficiently confident canonical mapping found for raw label "
                f"'{observation.raw_label}' under entity type '{observation.entity_type.value}'. "
                f"Best similarity score was {top_match.score:.3f}."
            )

        definition = self._definition_from_similarity_candidate(
            source_model=top_match.candidate.source_model,
            source_field=top_match.candidate.source_field,
            entity_type=observation.entity_type,
        )

        label_confidence = round(min(0.85, 0.45 + 0.5 * top_match.score), 4)
        return definition, label_confidence, top_match.score

    def _definition_from_similarity_candidate(
        self,
        source_model: str,
        source_field: str,
        entity_type: EntityType,
    ) -> CanonicalFieldDefinition:
        for definition in FLAT_FIELD_DEFINITIONS:
            if (
                definition.source_model == source_model
                and definition.source_field == source_field
                and definition.entity_type == entity_type
            ):
                return definition

        raise LabelMappingError(
            f"Similarity candidate could not be resolved back to a canonical definition "
            f"for source model '{source_model}', source field '{source_field}', "
            f"and entity type '{entity_type.value}'."
        )

    def _disambiguate_with_context(
        self,
        candidates: list[CanonicalFieldDefinition],
        source_node_type: str | None,
        neighbor_labels: list[str],
        raw_label: str,
        entity_type: EntityType,
    ) -> CanonicalFieldDefinition:
        """
        Choose the best candidate using lightweight node context.

        Current signals:
        - source_node_type matching the source model or entity type
        - overlap between neighbor labels and the candidate's field aliases
        """
        scored: list[tuple[float, CanonicalFieldDefinition]] = []

        for candidate in candidates:
            score = 0.0

            if source_node_type:
                normalized_node_type = self._normalize_text(source_node_type)

                if normalized_node_type == self._normalize_text(candidate.source_model):
                    score += 1.0

                if normalized_node_type == self._normalize_text(candidate.entity_type.value):
                    score += 0.75

            neighbor_tokens = {self._normalize_text(label) for label in neighbor_labels}
            candidate_tokens = {
                self._normalize_text(candidate.source_field),
                *(self._normalize_text(alias) for alias in candidate.allowed_raw_labels),
            }

            overlap = neighbor_tokens & candidate_tokens
            score += 0.1 * len(overlap)

            scored.append((score, candidate))

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].entity_type.value,
                item[1].source_model,
                item[1].source_field,
            )
        )

        top_score = scored[0][0]
        top_candidates = [candidate for score, candidate in scored if score == top_score]

        if len(top_candidates) != 1:
            raise LabelMappingError(
                f"Ambiguous canonical mapping for raw label '{raw_label}' "
                f"under entity type '{entity_type.value}'."
            )

        return top_candidates[0]

    def _context_confidence_bonus(
        self,
        definition: CanonicalFieldDefinition,
        source_node_type: str | None,
        neighbor_labels: list[str],
    ) -> float:
        """
        Add a small confidence bonus when the local node context supports
        the chosen definition.
        """
        bonus = 0.0

        if source_node_type:
            normalized_node_type = self._normalize_text(source_node_type)

            if normalized_node_type == self._normalize_text(definition.source_model):
                bonus += 0.03
            elif normalized_node_type == self._normalize_text(definition.entity_type.value):
                bonus += 0.02

        neighbor_tokens = {self._normalize_text(label) for label in neighbor_labels}
        candidate_tokens = {
            self._normalize_text(definition.source_field),
            *(self._normalize_text(alias) for alias in definition.allowed_raw_labels),
        }

        overlap_count = len(neighbor_tokens & candidate_tokens)
        bonus += min(0.02, 0.005 * overlap_count)

        return round(bonus, 4)

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