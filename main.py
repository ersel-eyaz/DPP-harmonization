# This is the entry point for the DPP harmonization sandbox.
# It loads a sample JSON-LD document, extracts raw observations,
# runs the harmonization pipeline, and prints the results.

from harmonizer import DataHarmonizer
from jsonld_ingestor import ingest_jsonld_document
from sample_jsonld_data import EXAMPLE_JSONLD_DOCUMENT
from utils import list_allowed_raw_labels, list_canonical_concepts


def main() -> None:
    print("DPP harmonization sandbox bootstrap loaded.")
    print()

    print("Canonical concepts:")
    for concept in list_canonical_concepts():
        print(f" - {concept}")
    print()

    print("Allowed raw labels:")
    for concept, labels in list_allowed_raw_labels().items():
        print(f" - {concept}: {labels}")
    print()

    print("Ingesting JSON-LD document...")
    raw_dataset = ingest_jsonld_document(EXAMPLE_JSONLD_DOCUMENT, source_system="jsonld_demo")

    print(f"Extracted raw observations: {len(raw_dataset.observations)}")
    for observation in raw_dataset.observations:
        print(
            f" - entity_type={observation.entity_type.value}, "
            f"entity_id={observation.entity_id}, "
            f"raw_label={observation.raw_label}, "
            f"raw_value={observation.raw_value}, "
            f"raw_unit={observation.raw_unit}"
        )

    print()
    print("Running harmonization...")
    harmonizer = DataHarmonizer()
    result = harmonizer.harmonize_dataset_container(raw_dataset)

    print()
    print("Harmonized records:")
    for record in result.dataset.records:
        print(
            f" - raw_label={record.raw_label}, "
            f"canonical_concept={record.canonical_concept.value}, "
            f"target_field={record.target_field}, "
            f"normalized_value={record.normalized_value}, "
            f"normalized_unit={record.normalized_unit}, "
            f"confidence={record.confidence}"
        )

    print()
    print(f"Unmapped observations: {len(result.unmapped)}")
    for item in result.unmapped:
        obs = item.observation
        print(
            f" - entity_type={obs.entity_type.value}, "
            f"entity_id={obs.entity_id}, "
            f"raw_label={obs.raw_label}, "
            f"reason={item.reason}"
        )


if __name__ == "__main__":
    main()