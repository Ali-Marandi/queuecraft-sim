"""Enterprise data-plane primitives for deterministic QueueCraft runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SchemaVersion:
    schema_id: str
    version: str
    compatible_with: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationProfile:
    profile_id: str
    required_fields: tuple[str, ...] = ()
    non_negative_fields: tuple[str, ...] = ()
    minimum_rows: int = 1


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    schema_id: str
    schema_version: str
    row_count: int
    column_names: tuple[str, ...]
    content_fingerprint: str
    quality_score: float | None = None


def validate_schema(schema: SchemaVersion) -> dict[str, Any]:
    if not schema.schema_id or not schema.version:
        raise ValueError("schema_id and version are required")
    return asdict(schema)


def validate_records(records: Sequence[Mapping[str, Any]], profile: ValidationProfile) -> dict[str, Any]:
    if len(records) < profile.minimum_rows:
        return {"valid": False, "status": "insufficient_rows", "row_count": len(records)}
    errors: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        for field in profile.required_fields:
            if field not in record or record[field] is None:
                errors.append({"row": index, "field": field, "reason": "missing"})
        for field in profile.non_negative_fields:
            value = record.get(field)
            if value is not None:
                try:
                    if float(value) < 0:
                        errors.append({"row": index, "field": field, "reason": "negative"})
                except (TypeError, ValueError):
                    errors.append({"row": index, "field": field, "reason": "not_numeric"})
    return {"valid": not errors, "status": "valid" if not errors else "invalid", "row_count": len(records), "errors": errors[:100]}


def build_dataset_manifest(*, dataset_id: str, records: Sequence[Mapping[str, Any]], schema: SchemaVersion, quality_score: float | None = None) -> dict[str, Any]:
    if quality_score is not None and not 0 <= quality_score <= 1:
        raise ValueError("quality_score must be between 0 and 1")
    columns = tuple(sorted({str(key) for row in records for key in row.keys()}))
    payload = {"dataset_id": dataset_id, "schema": asdict(schema), "records": list(records)}
    manifest = DatasetManifest(dataset_id, schema.schema_id, schema.version, len(records), columns, fingerprint(payload), quality_score)
    return asdict(manifest)


def build_cache_key(*, dataset_fingerprint: str, scenario_fingerprint: str, model_versions: Sequence[str], runtime_version: str) -> str:
    return fingerprint({"dataset": dataset_fingerprint, "scenario": scenario_fingerprint, "models": list(model_versions), "runtime": runtime_version})


def build_run_bundle(*, run_id: str, dataset_manifest: Mapping[str, Any], scenario: Mapping[str, Any], model_versions: Sequence[Mapping[str, Any]], seed: int | None, outputs: Mapping[str, Any]) -> dict[str, Any]:
    bundle = {
        "bundle_version": "1.0.0",
        "run_id": run_id,
        "dataset": dict(dataset_manifest),
        "scenario": dict(scenario),
        "models": [dict(item) for item in model_versions],
        "seed": seed,
        "outputs": dict(outputs),
    }
    bundle["bundle_fingerprint"] = fingerprint(bundle)
    return bundle
