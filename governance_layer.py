"""QueueCraft governance primitives: lineage, model registry, and evidence packs."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DataAsset:
    asset_id: str
    source_type: str
    description: str
    schema_version: str = "1.0"
    quality_score: float | None = None
    lineage_uri: str | None = None


@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    family: str
    version: str
    purpose: str
    status: str = "validated"
    limitations: tuple[str, ...] = ()


class GovernanceRegistry:
    """Small deterministic registry suitable for offline scenario evidence."""

    def __init__(self) -> None:
        self.data_assets: dict[str, DataAsset] = {}
        self.models: dict[str, ModelRecord] = {}

    def register_data(self, asset: DataAsset) -> DataAsset:
        if not 0.0 <= (asset.quality_score if asset.quality_score is not None else 1.0) <= 1.0:
            raise ValueError("quality_score must be between 0 and 1")
        self.data_assets[asset.asset_id] = asset
        return asset

    def register_model(self, model: ModelRecord) -> ModelRecord:
        self.models[model.model_id] = model
        return model

    def snapshot(self) -> dict[str, Any]:
        return {
            "data_assets": [asdict(x) for x in self.data_assets.values()],
            "models": [asdict(x) for x in self.models.values()],
        }


def data_quality_score(values: Sequence[Any], *, expected_min: int = 1) -> dict[str, Any]:
    """Return a transparent data-quality score from completeness/basic validity."""
    total = len(values)
    if total < expected_min:
        return {"score": 0.0, "completeness": 0.0, "valid_fraction": 0.0, "status": "insufficient"}
    present = sum(value is not None for value in values)
    valid = sum(value is not None and not (isinstance(value, float) and value != value) for value in values)
    completeness = present / total
    valid_fraction = valid / total
    score = round(0.5 * completeness + 0.5 * valid_fraction, 4)
    return {"score": score, "completeness": round(completeness, 4), "valid_fraction": round(valid_fraction, 4), "status": "good" if score >= 0.95 else "watch" if score >= 0.8 else "poor"}


def build_evidence_pack(*, decision: Mapping[str, Any], source_data: Sequence[DataAsset], models: Sequence[ModelRecord], assumptions: Mapping[str, Any], experiment: Mapping[str, Any] | None = None, approver: str | None = None) -> dict[str, Any]:
    """Create a portable, immutable-by-convention evidence record for a decision."""
    pack = {
        "evidence_version": "1.0.0",
        "decision": dict(decision),
        "source_data": [asdict(item) for item in source_data],
        "models": [asdict(item) for item in models],
        "assumptions": dict(assumptions),
        "experiment": dict(experiment or {}),
        "approval": {
            "required": True,
            "approver": approver,
            "status": "pending" if not approver else "approved",
        },
    }
    pack["evidence_fingerprint"] = fingerprint(pack)
    return pack
