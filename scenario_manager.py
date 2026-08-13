"""Enterprise scenario repository for QueueCraft.

Scenarios are versioned JSON documents with deterministic fingerprints. The
repository is local by default so no operational data leaves the customer's
machine. A future server-side repository can implement the same contract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "1.0"
DEFAULT_STORE = Path.home() / ".queuecraft" / "scenarios"


class ScenarioValidationError(ValueError):
    """Raised when a scenario cannot be reproduced safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize an AI–Monte Carlo scenario document."""
    if not isinstance(scenario, dict):
        raise ScenarioValidationError("scenario must be a JSON object")

    historical_counts = scenario.get("historical_counts")
    tiers = scenario.get("tiers")
    if not isinstance(historical_counts, list) or len(historical_counts) < 5:
        raise ScenarioValidationError("historical_counts must contain at least five values")
    if any(not isinstance(item, (int, float)) or item < 0 for item in historical_counts):
        raise ScenarioValidationError("historical_counts must be non-negative numbers")
    if not isinstance(tiers, list) or not tiers:
        raise ScenarioValidationError("tiers must be a non-empty array")

    names: set[str] = set()
    for index, tier in enumerate(tiers, start=1):
        if not isinstance(tier, dict):
            raise ScenarioValidationError(f"tier {index} must be an object")
        name = str(tier.get("name", "")).strip()
        if not name or name in names:
            raise ScenarioValidationError("every tier requires a unique non-empty name")
        names.add(name)
        if int(tier.get("servers", 0)) < 1:
            raise ScenarioValidationError(f"tier '{name}' requires at least one server")
        if float(tier.get("mean_service_time", 0)) <= 0:
            raise ScenarioValidationError(f"tier '{name}' requires a positive mean_service_time")
        if float(tier.get("service_cv", 1.0)) <= 0:
            raise ScenarioValidationError(f"tier '{name}' requires a positive service_cv")

    sla = scenario.get("sla", {})
    if sla is not None and not isinstance(sla, dict):
        raise ScenarioValidationError("sla must be an object when supplied")
    if isinstance(sla, dict) and sla.get("max_end_to_end_mean_wait") is not None:
        if float(sla["max_end_to_end_mean_wait"]) < 0:
            raise ScenarioValidationError("SLA maximum wait must be non-negative")

    normalized = {
        "schema_version": SCHEMA_VERSION,
        "name": str(scenario.get("name", "Untitled scenario")).strip() or "Untitled scenario",
        "description": str(scenario.get("description", "")).strip(),
        "historical_counts": [float(item) for item in historical_counts],
        "tiers": [
            {
                "name": str(tier["name"]).strip(),
                "servers": int(tier["servers"]),
                "mean_service_time": float(tier["mean_service_time"]),
                "service_cv": float(tier.get("service_cv", 1.0)),
            }
            for tier in tiers
        ],
        "simulation": {
            "horizon": int(scenario.get("simulation", {}).get("horizon", 5)),
            "replications": int(scenario.get("simulation", {}).get("replications", 500)),
            "seed": scenario.get("simulation", {}).get("seed", 42),
        },
        "sla": {
            "max_end_to_end_mean_wait": (
                None
                if not isinstance(sla, dict) or sla.get("max_end_to_end_mean_wait") is None
                else float(sla["max_end_to_end_mean_wait"])
            )
        },
        "metadata": dict(scenario.get("metadata", {})),
    }
    if normalized["simulation"]["horizon"] < 1 or normalized["simulation"]["replications"] < 30:
        raise ScenarioValidationError("simulation horizon must be positive and replications must be at least 30")
    return normalized


def evaluate_sla(simulation_result: dict[str, Any], max_mean_wait: float | None) -> dict[str, Any]:
    """Create an explicit, audit-friendly SLA assessment from a simulation result."""
    observed_wait = float(simulation_result["simulation"]["end_to_end_mean_wait"])
    if max_mean_wait is None:
        return {"configured": False, "status": "not_configured", "observed_mean_wait": observed_wait}
    return {
        "configured": True,
        "status": "pass" if observed_wait <= max_mean_wait else "fail",
        "threshold": max_mean_wait,
        "observed_mean_wait": observed_wait,
        "variance_from_threshold": round(observed_wait - max_mean_wait, 3),
    }


@dataclass
class ScenarioRepository:
    store_path: Path = DEFAULT_STORE

    def __post_init__(self) -> None:
        self.store_path = Path(self.store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

    def _path(self, scenario_id: str) -> Path:
        if not scenario_id or any(character in scenario_id for character in "/\\"):
            raise ScenarioValidationError("scenario id is invalid")
        return self.store_path / f"{scenario_id}.json"

    def save(self, scenario: dict[str, Any], scenario_id: str | None = None) -> dict[str, Any]:
        normalized = validate_scenario(scenario)
        current_id = scenario_id or str(scenario.get("id") or uuid4())
        destination = self._path(current_id)
        existing = self.load(current_id) if destination.exists() else None
        saved_at = utc_now()
        document = {
            "id": current_id,
            "created_at": existing["created_at"] if existing else saved_at,
            "updated_at": saved_at,
            "scenario": normalized,
        }
        document["fingerprint"] = fingerprint(document["scenario"])
        destination.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return document

    def load(self, scenario_id: str) -> dict[str, Any]:
        source = self._path(scenario_id)
        if not source.exists():
            raise FileNotFoundError(f"scenario '{scenario_id}' does not exist")
        document = json.loads(source.read_text(encoding="utf-8"))
        if fingerprint(document["scenario"]) != document.get("fingerprint"):
            raise ScenarioValidationError("scenario fingerprint verification failed")
        return document

    def list(self) -> list[dict[str, Any]]:
        summaries = []
        for source in sorted(self.store_path.glob("*.json")):
            document = self.load(source.stem)
            summaries.append(
                {
                    "id": document["id"],
                    "name": document["scenario"]["name"],
                    "updated_at": document["updated_at"],
                    "fingerprint": document["fingerprint"],
                }
            )
        return summaries

    def delete(self, scenario_id: str) -> None:
        source = self._path(scenario_id)
        if not source.exists():
            raise FileNotFoundError(f"scenario '{scenario_id}' does not exist")
        source.unlink()
