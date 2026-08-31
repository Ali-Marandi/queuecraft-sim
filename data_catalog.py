"""Local data catalog and run registry for QueueCraft Enterprise AI."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from data_plane import build_cache_key, fingerprint


@dataclass
class FeatureDefinition:
    feature_id: str
    name: str
    version: str
    source_dataset_ids: tuple[str, ...] = ()
    description: str = ""
    tags: tuple[str, ...] = ()
    status: str = "active"


@dataclass
class DatasetRecord:
    dataset_id: str
    version: str
    content_fingerprint: str
    schema_id: str
    schema_version: str
    status: str = "active"
    tags: tuple[str, ...] = ()
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RunRecord:
    run_id: str
    dataset_fingerprints: tuple[str, ...]
    scenario_fingerprint: str
    model_versions: tuple[str, ...]
    runtime_version: str
    cache_key: str
    status: str = "completed"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DataCatalog:
    """In-memory catalog contract; a persistent backend can implement the same API."""

    def __init__(self) -> None:
        self.datasets: dict[str, DatasetRecord] = {}
        self.features: dict[str, FeatureDefinition] = {}
        self.runs: dict[str, RunRecord] = {}

    def register_dataset(self, record: DatasetRecord) -> DatasetRecord:
        if not record.dataset_id or not record.version or not record.content_fingerprint:
            raise ValueError("dataset_id, version and content_fingerprint are required")
        self.datasets[record.dataset_id] = record
        return record

    def register_feature(self, feature: FeatureDefinition) -> FeatureDefinition:
        if not feature.feature_id or not feature.name or not feature.version:
            raise ValueError("feature_id, name and version are required")
        missing = [item for item in feature.source_dataset_ids if item not in self.datasets]
        if missing:
            raise ValueError(f"unknown source datasets: {missing}")
        self.features[feature.feature_id] = feature
        return feature

    def record_run(self, *, run_id: str, dataset_fingerprints: tuple[str, ...], scenario_fingerprint: str, model_versions: tuple[str, ...], runtime_version: str, status: str = "completed") -> RunRecord:
        cache_key = build_cache_key(
            dataset_fingerprint=fingerprint(sorted(dataset_fingerprints)),
            scenario_fingerprint=scenario_fingerprint,
            model_versions=model_versions,
            runtime_version=runtime_version,
        )
        run = RunRecord(run_id, dataset_fingerprints, scenario_fingerprint, model_versions, runtime_version, cache_key, status)
        self.runs[run_id] = run
        return run

    def usage(self, dataset_id: str) -> dict[str, Any]:
        if dataset_id not in self.datasets:
            raise KeyError(dataset_id)
        features = [feature.feature_id for feature in self.features.values() if dataset_id in feature.source_dataset_ids]
        runs = []
        dataset_fp = self.datasets[dataset_id].content_fingerprint
        for run in self.runs.values():
            if dataset_fp in run.dataset_fingerprints:
                runs.append(run.run_id)
        return {"dataset_id": dataset_id, "features": sorted(features), "runs": sorted(runs)}

    def snapshot(self) -> dict[str, Any]:
        return {
            "datasets": [asdict(item) for item in self.datasets.values()],
            "features": [asdict(item) for item in self.features.values()],
            "runs": [asdict(item) for item in self.runs.values()],
        }


def cache_invalidation_reason(*, old_dataset_fingerprint: str, new_dataset_fingerprint: str, scenario_fingerprint: str, model_versions: tuple[str, ...], runtime_version: str) -> dict[str, Any]:
    old_key = build_cache_key(dataset_fingerprint=old_dataset_fingerprint, scenario_fingerprint=scenario_fingerprint, model_versions=model_versions, runtime_version=runtime_version)
    new_key = build_cache_key(dataset_fingerprint=new_dataset_fingerprint, scenario_fingerprint=scenario_fingerprint, model_versions=model_versions, runtime_version=runtime_version)
    return {"invalidated": old_key != new_key, "old_cache_key": old_key, "new_cache_key": new_key, "reason": "dataset_fingerprint_changed" if old_key != new_key else "unchanged_inputs"}
