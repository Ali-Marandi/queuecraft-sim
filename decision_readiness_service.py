"""JSON service/CLI for the governed QueueCraft readiness gate."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

from decision_readiness import evaluate_readiness


def evaluate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    required = payload.get("required_evidence_fields", ())
    if not isinstance(required, list):
        raise ValueError("required_evidence_fields must be a list")
    now_value = payload.get("now")
    now = None
    if now_value:
        text = str(now_value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        now = datetime.fromisoformat(text).astimezone(timezone.utc)
    return evaluate_readiness(
        envelope=payload.get("envelope", {}),
        decision=payload.get("decision", {}),
        evidence=payload.get("evidence", {}),
        policy_result=payload.get("policy_result", {}),
        approval=payload.get("approval"),
        required_evidence_fields=required,
        now=now,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a QueueCraft decision readiness payload")
    parser.add_argument("path", nargs="?", help="JSON payload file; stdin is used when omitted")
    args = parser.parse_args(argv)
    try:
        raw = open(args.path, encoding="utf-8").read() if args.path else sys.stdin.read()
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        result = evaluate_payload(payload)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["ready"] else 2 if result["blocked"] else 3
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
