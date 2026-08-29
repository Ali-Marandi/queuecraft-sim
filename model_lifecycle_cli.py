"""QueueCraft model lifecycle console."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_lifecycle import ModelCandidate, compare_challengers, model_lifecycle_snapshot


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="QueueCraft model lifecycle console")
    parser.add_argument("scenario", help="Model lifecycle JSON scenario")
    parser.add_argument("--output", help="Write lifecycle result JSON")
    args = parser.parse_args()
    payload = _load(args.scenario)
    models = [
        ModelCandidate(
            item["model_id"], item["family"], item["version"],
            item["metrics"], tuple(item.get("limitations", [])),
        )
        for item in payload["models"]
    ]
    comparison = compare_challengers(
        models,
        primary_metric=payload.get("primary_metric", "rmse"),
        tolerance=float(payload.get("tolerance", 0.0)),
    )
    result = {"comparison": comparison}
    snapshot_model = next(model for model in models if model.model_id == payload.get("snapshot_model_id", models[0].model_id))
    if "actual" in payload and "predicted" in payload:
        result["snapshot"] = model_lifecycle_snapshot(
            model=snapshot_model,
            actual=payload["actual"],
            predicted=payload["predicted"],
            reference_load=payload.get("reference_load"),
            current_load=payload.get("current_load"),
        )
    print("QueueCraft — Model Lifecycle")
    print(f"Recommended challenger : {comparison['recommended_candidate']}")
    print(f"Automatic promotion    : {comparison['promotion']['automatic']}")
    if result.get("snapshot", {}).get("input_drift"):
        print(f"Input drift             : {result['snapshot']['input_drift']['status']}")
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Saved lifecycle        : {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
