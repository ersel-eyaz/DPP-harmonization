# Generic JSON-LD ingestion layer for the DPP harmonization sandbox.
# It traverses JSON-LD nodes and extracts scalar/value-object properties
# into RawObservation objects without hardcoding field names.

from __future__ import annotations

from typing import Any

from dataset import RawDataset
from enums import EntityType
from schemas import RawObservation


class JSONLDIngestionError(ValueError):
    """Raised when a JSON-LD document cannot be ingested."""


TYPE_TO_ENTITY = {
    "Product": EntityType.DPP_INSTANCE,
    "ProductModel": EntityType.DPP_INSTANCE,
    "DPPInstance": EntityType.DPP_INSTANCE,
    "Material": EntityType.MATERIAL_INSTANCE,
    "MaterialInstance": EntityType.MATERIAL_INSTANCE,
    "TransferAction": EntityType.TRANSPORT_STEP,
    "TransportStep": EntityType.TRANSPORT_STEP,
    "GHGEmissionRecord": EntityType.GHG_EMISSION_RECORD,
}


def ingest_jsonld_document(document: dict[str, Any], source_system: str = "jsonld_input") -> RawDataset:
    dataset = RawDataset()

    if not isinstance(document, dict):
        raise JSONLDIngestionError("JSON-LD document must be a dictionary.")

    if "@graph" in document:
        graph = document["@graph"]
        if not isinstance(graph, list):
            raise JSONLDIngestionError("'@graph' must be a list.")
        for node in graph:
            _extract_node(node=node, dataset=dataset, source_system=source_system)
    else:
        _extract_node(node=document, dataset=dataset, source_system=source_system)

    return dataset


def _extract_node(node: dict[str, Any], dataset: RawDataset, source_system: str) -> None:
    if not isinstance(node, dict):
        return

    entity_type = _resolve_entity_type(node)
    if entity_type is None:
        return

    entity_id = _resolve_entity_id(node)

    for key, value in node.items():
        if key in {"@context", "@id", "@type"}:
            continue

        raw_label = _strip_prefix(key)
        extracted_items = _extract_property_values(value)

        for raw_value, raw_unit in extracted_items:
            dataset.add(
                RawObservation(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    raw_label=raw_label,
                    raw_value=raw_value,
                    raw_unit=raw_unit,
                    source_system=source_system,
                    source_file="jsonld_document",
                )
            )


def _extract_property_values(value: Any) -> list[tuple[Any, str | None]]:
    """
    Returns a list of (raw_value, raw_unit) pairs extracted from a JSON-LD property value.
    Supports:
    - scalar literals
    - value objects like {"@value": 120, "unitCode": "h"}
    - lists of literals / value objects
    """
    results: list[tuple[Any, str | None]] = []

    if _is_scalar(value):
        results.append((value, None))
        return results

    if isinstance(value, dict):
        literal = _extract_literal_from_dict(value)
        if literal is not None:
            raw_value, raw_unit = literal
            results.append((raw_value, raw_unit))
        return results

    if isinstance(value, list):
        for item in value:
            results.extend(_extract_property_values(item))
        return results

    return results


def _extract_literal_from_dict(value: dict[str, Any]) -> tuple[Any, str | None] | None:
    if "@value" in value:
        raw_unit = _extract_unit(value)
        return value["@value"], raw_unit

    # simple value object fallback: {"value": 120, "unit": "h"}
    if "value" in value:
        raw_unit = _extract_unit(value)
        return value["value"], raw_unit

    return None


def _extract_unit(value: dict[str, Any]) -> str | None:
    for key in ("unitCode", "unit", "rawUnit"):
        unit = value.get(key)
        if isinstance(unit, str) and unit.strip():
            return unit.strip()
    return None


def _resolve_entity_type(node: dict[str, Any]) -> EntityType | None:
    raw_type = node.get("@type")
    if raw_type is None:
        return None

    candidates = raw_type if isinstance(raw_type, list) else [raw_type]

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue
        simplified = _strip_prefix(candidate)
        entity_type = TYPE_TO_ENTITY.get(simplified)
        if entity_type is not None:
            return entity_type

    return None


def _resolve_entity_id(node: dict[str, Any]) -> str | None:
    raw_id = node.get("@id") or node.get("id")
    if raw_id is None:
        return None
    return str(raw_id)


def _strip_prefix(value: str) -> str:
    if ":" in value:
        return value.split(":")[-1]
    return value


def _is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool))