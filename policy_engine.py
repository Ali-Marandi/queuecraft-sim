"""Policy evaluation for governed QueueCraft decisions.

Policies are declarative, deterministic, and side-effect free. They evaluate a
result against thresholds and return an auditable allow/review/block decision.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Sequence


OPERATORS = {"gte", "gt", "lte", "lt", "eq", "neq", "in"}
ACTIONS = {"allow", "review", "block"}


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    field: str
    operator: str
    value: Any
    action: str = "review"
    reason: str = ""
    priority: int = 100

    def validate(self) -> None:
        if not self.rule_id or not self.field:
            raise ValueError("rule_id and field are required")
        if self.operator not in OPERATORS:
            raise ValueError(f"unsupported operator: {self.operator}")
        if self.action not in ACTIONS:
            raise ValueError(f"unsupported action: {self.action}")


@dataclass(frozen=True)
class PolicySet:
    policy_id: str
    version: str
    rules: tuple[PolicyRule, ...]
    default_action: str = "review"

    def validate(self) -> None:
        if not self.policy_id or not self.version:
            raise ValueError("policy_id and version are required")
        if self.default_action not in ACTIONS:
            raise ValueError("default_action must be allow, review, or block")
        ids: set[str] = set()
        for rule in self.rules:
            rule.validate()
            if rule.rule_id in ids:
                raise ValueError(f"duplicate rule_id: {rule.rule_id}")
            ids.add(rule.rule_id)


def _get_field(payload: Mapping[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _matches(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "gte": return actual >= expected
    if operator == "gt": return actual > expected
    if operator == "lte": return actual <= expected
    if operator == "lt": return actual < expected
    if operator == "eq": return actual == expected
    if operator == "neq": return actual != expected
    if operator == "in": return actual in expected
    raise ValueError(f"unsupported operator: {operator}")


def evaluate_policy(policy: PolicySet, decision: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate all matching rules; the strongest action wins: block > review > allow."""
    policy.validate()
    if not isinstance(decision, Mapping):
        raise ValueError("decision must be a mapping")
    ranked = {"allow": 0, "review": 1, "block": 2}
    checks: list[dict[str, Any]] = []
    matched: list[PolicyRule] = []
    for rule in sorted(policy.rules, key=lambda item: (item.priority, item.rule_id)):
        present, actual = _get_field(decision, rule.field)
        if not present:
            checks.append({"rule_id": rule.rule_id, "status": "not_evaluable", "field": rule.field})
            continue
        try:
            hit = _matches(actual, rule.operator, rule.value)
        except TypeError:
            hit = False
        checks.append({
            "rule_id": rule.rule_id,
            "field": rule.field,
            "actual": actual,
            "operator": rule.operator,
            "expected": rule.value,
            "matched": hit,
            "action": rule.action,
            "status": "matched" if hit else "pass",
        })
        if hit:
            matched.append(rule)
    action = policy.default_action
    if matched:
        action = max((rule.action for rule in matched), key=lambda value: ranked[value])
    return {
        "policy": {"policy_id": policy.policy_id, "version": policy.version},
        "action": action,
        "allowed": action == "allow",
        "review_required": action == "review",
        "blocked": action == "block",
        "matched_rules": [asdict(rule) for rule in matched],
        "checks": checks,
    }


def policy_from_mapping(payload: Mapping[str, Any]) -> PolicySet:
    if not isinstance(payload, Mapping):
        raise ValueError("policy payload must be an object")
    rules = tuple(
        PolicyRule(
            str(item["rule_id"]), str(item["field"]), str(item["operator"]), item.get("value"),
            str(item.get("action", "review")), str(item.get("reason", "")), int(item.get("priority", 100)),
        )
        for item in payload.get("rules", [])
    )
    policy = PolicySet(str(payload["policy_id"]), str(payload["version"]), rules, str(payload.get("default_action", "review")))
    policy.validate()
    return policy
