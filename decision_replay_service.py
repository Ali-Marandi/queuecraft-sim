"""JSON service contract for QueueCraft decision replay."""
from __future__ import annotations

import json
from typing import Any, Callable

from decision_replay import replay_decision, replay_snapshot


def build_replay_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    return replay_snapshot(payload)


def replay_json(payload_json: str, executor: Callable[[dict[str, Any]], dict[str, Any]]) -> str:
    try:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        result = replay_decision(payload, executor, expected_fingerprint=payload.get("decision_fingerprint"))
        return json.dumps(result.to_dict(), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)


def identity_executor(evidence: dict[str, Any]) -> dict[str, Any]:
    decision = evidence.get("decision", evidence.get("result", evidence))
    if not isinstance(decision, dict):
        raise ValueError("evidence decision must be an object")
    return decision


if __name__ == "__main__":
    import sys
    payload = sys.stdin.read() if len(sys.argv) == 1 else open(sys.argv[1], encoding="utf-8").read()
    print(replay_json(payload, identity_executor))
