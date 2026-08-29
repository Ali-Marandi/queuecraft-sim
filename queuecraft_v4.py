"""QueueCraft v4 decision console.

Builds an offline-first decision package from a JSON scenario. The command
prints a compact executive summary and can persist the complete auditable
package as JSON. It never applies operational changes or calls cloud APIs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from decision_engine import build_decision_package

DEFAULT_SCENARIO = {
    "historical_counts": [8, 11, 13, 19, 22, 24, 20, 18, 21, 27, 31, 34],
    "tiers": [
        {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
        {"name": "Consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
    ],
    "sla_mean_wait": 5.0,
    "cost_per_server": 1.0,
    "server_range": [1, 6],
    "replications": 120,
    "seed": 42,
}


def _load(path: str | None) -> dict:
    if not path:
        return DEFAULT_SCENARIO
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="QueueCraft v4 decision console")
    parser.add_argument("scenario", nargs="?", help="Path to a scenario JSON file")
    parser.add_argument("--output", help="Write the full decision package to JSON")
    parser.add_argument("--llm", action="store_true", help="Explicitly enable the constrained LLM advisor")
    parser.add_argument("--model", default="gpt-5-mini")
    args = parser.parse_args()

    scenario = _load(args.scenario)
    package = build_decision_package(
        scenario["historical_counts"], scenario["tiers"],
        sla_mean_wait=scenario.get("sla_mean_wait"),
        cost_per_server=float(scenario.get("cost_per_server", 1.0)),
        server_range=tuple(scenario.get("server_range", [1, 6])),
        replications=int(scenario.get("replications", 120)),
        seed=scenario.get("seed", 42),
        arrival_multipliers=scenario.get("arrival_multipliers", [0.8, 1.0, 1.2]),
        service_time_multipliers=scenario.get("service_time_multipliers", [0.8, 1.0, 1.2]),
        enable_llm=args.llm,
        model=args.model,
        constraints=scenario.get("constraints"),
    )

    baseline = package["benchmark"]["baseline"]
    proposed = package["benchmark"]["proposed"]
    risk = package["risk"]
    recommendation = package["recommendation"]
    print("QueueCraft 4 — Decision Console")
    print(f"Baseline mean wait : {baseline['mean_wait']:.3f}")
    print(f"Proposed mean wait : {proposed['mean_wait']:.3f}")
    print(f"Proposed capacity  : {proposed['servers']}")
    print(f"SLA status         : {risk['sla']['status']}")
    print(f"Risk indicator     : {risk['screening_sla_failure_risk']}")
    print(f"Recommendation     : {recommendation['selected_candidate']['candidate_id']}")
    print(f"Approval required   : {package['approval']['required']}")
    print(f"Package fingerprint : {package['package_fingerprint']}")

    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Saved package      : {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
