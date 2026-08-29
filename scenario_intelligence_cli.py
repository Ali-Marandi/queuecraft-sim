"""CLI for QueueCraft Scenario Intelligence 2.0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scenario_intelligence import run_integrated_scenario


def main() -> int:
    parser = argparse.ArgumentParser(description="QueueCraft Scenario Intelligence 2.0")
    parser.add_argument("scenario", help="Integrated market + operational scenario JSON")
    parser.add_argument("--output", help="Write complete scenario package JSON")
    args = parser.parse_args()

    payload = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    result = run_integrated_scenario(payload)
    graph = result["scenario_graph"]
    print("QueueCraft — Scenario Intelligence 2.0")
    print(f"Macro regime        : {result['market']['macro']['regime']}")
    print(f"Market stress       : {result['market']['stress']['severity']}")
    print(f"Operational risk    : {result['operations']['risk']['status']}")
    print(f"Top graph driver    : {graph['ranking'][0]['node'] if graph['ranking'] else 'none'}")
    print(f"Counterfactual pts  : {len(result['counterfactual']['transformed_history'])}")
    print(f"Approval required   : {result['governance']['controls']['human_approval_required']}")
    print(f"Scenario fingerprint: {result['scenario_fingerprint']}")

    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Saved package       : {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
