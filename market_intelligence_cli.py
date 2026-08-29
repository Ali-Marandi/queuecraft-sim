"""CLI for QueueCraft's cross-disciplinary market intelligence engine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from market_intelligence import analyze_market_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="QueueCraft market intelligence console")
    parser.add_argument("scenario", help="JSON snapshot with macro/factor/risk inputs")
    parser.add_argument("--output", help="Write the complete analysis JSON")
    args = parser.parse_args()

    snapshot = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    result = analyze_market_snapshot(snapshot)
    print("QueueCraft — Market Intelligence")
    print(f"Macro regime       : {result['macro']['regime']}")
    print(f"Taylor rule gap    : {result['macro']['policy_vs_rule_gap']:.3f}")
    if result["factor_model"]:
        print(f"Factor R²          : {result['factor_model']['r_squared']:.3f}")
    if result["volatility"]:
        print(f"1-step volatility  : {result['volatility']['volatility_forecast'][0]:.6f}")
    print(f"Stress severity     : {result['stress']['severity']}")
    print(f"Behavior proxy risk : {result['behavior']['concentration_risk']:.3f}")
    print("Research frontier   : DSGE / causal ML / TDA / diffusion / quantum / federated learning remain research-only")

    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Saved analysis      : {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
