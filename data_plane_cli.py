"""CLI for validating a dataset manifest and creating a reproducible run bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_plane import SchemaVersion, ValidationProfile, build_dataset_manifest, build_run_bundle, validate_records


def main() -> int:
    parser = argparse.ArgumentParser(description="QueueCraft Enterprise Data Plane")
    parser.add_argument("input", help="JSON file with records")
    parser.add_argument("--output", default="artifacts/run-bundle.json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise SystemExit("input must contain a records array")
    schema = SchemaVersion(str(payload.get("schema_id", "queuecraft.dataset")), str(payload.get("schema_version", "1.0")))
    profile = ValidationProfile(
        str(payload.get("validation_profile", "default")),
        tuple(payload.get("required_fields", [])),
        tuple(payload.get("non_negative_fields", [])),
        int(payload.get("minimum_rows", 1)),
    )
    validation = validate_records(payload["records"], profile)
    if not validation["valid"]:
        raise SystemExit(json.dumps(validation, ensure_ascii=False))
    manifest = build_dataset_manifest(dataset_id=str(payload.get("dataset_id", "dataset-1")), records=payload["records"], schema=schema, quality_score=payload.get("quality_score"))
    bundle = build_run_bundle(
        run_id=str(payload.get("run_id", "run-1")),
        dataset_manifest=manifest,
        scenario=payload.get("scenario", {}),
        model_versions=payload.get("models", []),
        seed=payload.get("seed"),
        outputs=payload.get("outputs", {}),
    )
    bundle["validation"] = validation
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(destination), "bundle_fingerprint": bundle["bundle_fingerprint"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
