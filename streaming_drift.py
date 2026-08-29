from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from statistics import mean
from typing import Sequence


@dataclass(frozen=True)
class DriftThresholds:
    mean_shift_ratio: float = 0.20
    std_shift_ratio: float = 0.25
    ks_proxy_ratio: float = 0.20
    min_reference: int = 20
    min_current: int = 10


def _safe_ratio(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-12)


def _cdf_distance(reference: Sequence[float], current: Sequence[float]) -> float:
    ref = sorted(float(x) for x in reference)
    cur = sorted(float(x) for x in current)
    points = sorted(set(ref + cur))
    if not points:
        return 0.0
    r = c = 0
    distance = 0.0
    for p in points:
        while r < len(ref) and ref[r] <= p:
            r += 1
        while c < len(cur) and cur[c] <= p:
            c += 1
        distance = max(distance, abs(r / len(ref) - c / len(cur)))
    return float(distance)


def drift_report(reference: Sequence[float], current: Sequence[float], thresholds: DriftThresholds | None = None) -> dict:
    t = thresholds or DriftThresholds()
    if len(reference) < t.min_reference or len(current) < t.min_current:
        return {"status": "insufficient_data", "trigger": False, "metrics": {}}
    ref_mean = mean(reference)
    cur_mean = mean(current)
    ref_std = sqrt(sum((x - ref_mean) ** 2 for x in reference) / max(len(reference) - 1, 1))
    cur_std = sqrt(sum((x - cur_mean) ** 2 for x in current) / max(len(current) - 1, 1))
    metrics = {
        "mean_shift_ratio": round(_safe_ratio(cur_mean, ref_mean), 6),
        "std_shift_ratio": round(_safe_ratio(cur_std, ref_std), 6),
        "ks_proxy": round(_cdf_distance(reference, current), 6),
    }
    triggers = {
        "mean_shift": metrics["mean_shift_ratio"] >= t.mean_shift_ratio,
        "std_shift": metrics["std_shift_ratio"] >= t.std_shift_ratio,
        "distribution_shift": metrics["ks_proxy"] >= t.ks_proxy_ratio,
    }
    fired = [name for name, value in triggers.items() if value]
    return {
        "status": "drift_detected" if fired else "stable",
        "trigger": bool(fired),
        "reasons": fired,
        "metrics": metrics,
        "thresholds": {
            "mean_shift_ratio": t.mean_shift_ratio,
            "std_shift_ratio": t.std_shift_ratio,
            "ks_proxy_ratio": t.ks_proxy_ratio,
        },
    }


@dataclass
class StreamingDriftMonitor:
    reference: list[float] = field(default_factory=list)
    current: list[float] = field(default_factory=list)
    thresholds: DriftThresholds = field(default_factory=DriftThresholds)
    max_reference: int = 500
    max_current: int = 100

    def seed_reference(self, values: Sequence[float]) -> dict:
        self.reference = [float(v) for v in values][-self.max_reference :]
        self.current = []
        return self.snapshot()

    def ingest(self, values: Sequence[float]) -> dict:
        self.current.extend(float(v) for v in values)
        self.current = self.current[-self.max_current :]
        return self.evaluate()

    def evaluate(self) -> dict:
        report = drift_report(self.reference, self.current, self.thresholds)
        return {"report": report, "challenger_trigger": self.challenger_trigger(report)}

    @staticmethod
    def challenger_trigger(report: dict) -> dict:
        return {
            "evaluation_requested": bool(report.get("trigger")),
            "action": "create_challenger_evaluation" if report.get("trigger") else "none",
            "deployment": "blocked",
            "reason": report.get("reasons", []),
        }

    def reset_current(self) -> dict:
        self.current = []
        return self.snapshot()

    def snapshot(self) -> dict:
        return {"reference_size": len(self.reference), "current_size": len(self.current), "max_reference": self.max_reference, "max_current": self.max_current}
