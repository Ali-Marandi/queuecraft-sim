"""Deterministic experiment registry for governed QueueCraft runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from governance_hardening import fingerprint


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    name: str
    version: str
    model_versions: tuple[str, ...]
    seed: int | None
    parameters: Mapping[str, Any]
    objective: str

    def validate(self) -> None:
        for field in ("experiment_id", "name", "version", "objective"):
            if not str(getattr(self, field)).strip():
                raise ValueError(f"{field} is required")
        if not self.model_versions:
            raise ValueError("at least one model version is required")

    def identity(self) -> str:
        self.validate()
        return fingerprint(asdict(self))


def register_experiment(spec: ExperimentSpec) -> dict[str, Any]:
    spec.validate()
    return {**asdict(spec), "model_versions": list(spec.model_versions), "experiment_fingerprint": spec.identity()}


def compare_metrics(baseline: Mapping[str, float], challenger: Mapping[str, float], *, higher_is_better: Sequence[str] = ()) -> dict[str, Any]:
    if not baseline or not challenger:
        raise ValueError("baseline and challenger metrics are required")
    higher = set(higher_is_better)
    rows = []
    for metric in sorted(set(baseline) & set(challenger)):
        before = float(baseline[metric])
        after = float(challenger[metric])
        delta = after - before
        improved = delta > 0 if metric in higher else delta < 0
        rows.append({"metric": metric, "baseline": before, "challenger": after, "delta": delta, "improved": improved})
    return {"metrics_compared": len(rows), "rows": rows, "improved_metrics": sum(item["improved"] for item in rows)}


def build_experiment_run(spec: ExperimentSpec, *, dataset_fingerprint: str, outputs: Mapping[str, Any], metrics: Mapping[str, float], started_at: str | None = None) -> dict[str, Any]:
    spec.validate()
    if len(dataset_fingerprint) != 64:
        raise ValueError("dataset_fingerprint must be a SHA-256 digest")
    run = {
        "run_schema_version": 1,
        "experiment": register_experiment(spec),
        "dataset_fingerprint": dataset_fingerprint,
        "started_at": started_at or datetime.now(timezone.utc).isoformat(),
        "outputs": dict(outputs),
        "metrics": {str(k): float(v) for k, v in metrics.items()},
    }
    run["run_fingerprint"] = fingerprint(run)
    return run
