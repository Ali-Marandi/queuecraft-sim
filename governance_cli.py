"""QueueCraft offline governance console."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from decision_engine import build_decision_package
from governance_layer import DataAsset, ModelRecord, build_evidence_pack, data_quality_score


def main() -> int:
    parser = argparse.ArgumentParser(description="QueueCraft governance evidence pack")
    parser.add_argument("scenario", help="Scenario JSON")
    parser.add_argument("--output", required=True, help="Evidence pack JSON output")
    args = parser.parse_args()

    raw = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    history = raw["historical_counts"]
    tiers = raw["tiers"]
    package = build_decision_package(
        history, tiers,
        sla_mean_wait=raw.get("sla_mean_wait"),
        cost_per_server=float(raw.get("cost_per_server", 1.0)),
        server_range=tuple(raw.get("server_range", [1, 6])),
        replications=int(raw.get("replications", 120)),
        seed=raw.get("seed", 42),
        arrival_multipliers=raw.get("arrival_multipliers", [0.8, 1.0, 1.2]),
        service_time_multipliers=raw.get("service_time_multipliers", [0.8, 1.0, 1.2]),
        constraints=raw.get("constraints"),
    )
    quality = data_quality_score(history, expected_min=5)
    data = [DataAsset("historical-arrivals", "scenario-json", "Historical arrival buckets", quality_score=quality["score"])]
    models = [
        ModelRecord("decision-engine", "capacity-optimization", package["version"], "Cost/SLA capacity recommendation"),
        ModelRecord("market-intelligence", "cross-disciplinary-screening", "1.0.0", "Optional market context analysis", limitations=("Not a live trading signal",)),
    ]
    pack = build_evidence_pack(
        decision={"recommendation": package["recommendation"], "package_fingerprint": package["package_fingerprint"]},
        source_data=data,
        models=models,
        assumptions=raw,
        experiment=raw.get("experiment"),
    )
    pack["data_quality"] = quality
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("QueueCraft — Governance Evidence Pack")
    print(f"Data quality       : {quality['score']:.3f} ({quality['status']})")
    print(f"Decision fingerprint: {package['package_fingerprint']}")
    print(f"Evidence fingerprint: {pack['evidence_fingerprint']}")
    print(f"Approval status    : {pack['approval']['status']}")
    print(f"Saved              : {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
