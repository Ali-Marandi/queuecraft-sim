"""Controlled Generative AI advisor for QueueCraft v4.0.

The advisor turns *already evaluated* Pareto candidates into a constrained,
auditable recommendation. It never fabricates a capacity plan outside the
candidate catalog, never applies changes, and only calls an LLM when callers
explicitly set enable_llm=True.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from typing import Any, Mapping, Sequence


DEFAULT_MODEL = "gpt-5-mini"


@dataclass(frozen=True)
class AdvisorConstraints:
    max_mean_wait: float | None = None
    max_server_cost: float | None = None
    require_sla_compliance: bool = True

    def validate(self) -> None:
        if self.max_mean_wait is not None and self.max_mean_wait < 0:
            raise ValueError("max_mean_wait must be non-negative when supplied")
        if self.max_server_cost is not None and self.max_server_cost < 0:
            raise ValueError("max_server_cost must be non-negative when supplied")


def _canonical_fingerprint(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(rendered.encode("utf-8")).hexdigest()


def _coerce_constraints(value: AdvisorConstraints | Mapping[str, Any] | None) -> AdvisorConstraints:
    result = value if isinstance(value, AdvisorConstraints) else AdvisorConstraints(**(value or {}))
    result.validate()
    return result


def _candidate_catalog(pareto_analysis: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = pareto_analysis.get("pareto_frontier") or pareto_analysis.get("candidates")
    if not isinstance(candidates, Sequence) or not candidates:
        raise ValueError("pareto analysis must contain a non-empty pareto_frontier or candidates array")
    catalog: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise ValueError("each candidate must be an object")
        required = {"servers", "server_cost", "mean_wait", "p95_wait", "mean_utilization_pct"}
        missing = required - set(candidate)
        if missing:
            raise ValueError(f"candidate is missing required values: {sorted(missing)}")
        catalog.append(
            {
                "candidate_id": f"plan-{index + 1}",
                "servers": list(candidate["servers"]),
                "server_cost": float(candidate["server_cost"]),
                "mean_wait": float(candidate["mean_wait"]),
                "p95_wait": float(candidate["p95_wait"]),
                "mean_utilization_pct": float(candidate["mean_utilization_pct"]),
                "sla_compliant": candidate.get("sla_compliant"),
            }
        )
    return catalog


def _eligible_candidates(catalog: Sequence[dict[str, Any]], constraints: AdvisorConstraints) -> list[dict[str, Any]]:
    eligible = []
    for candidate in catalog:
        if constraints.require_sla_compliance and candidate["sla_compliant"] is not True:
            continue
        if constraints.max_mean_wait is not None and candidate["mean_wait"] > constraints.max_mean_wait:
            continue
        if constraints.max_server_cost is not None and candidate["server_cost"] > constraints.max_server_cost:
            continue
        eligible.append(candidate)
    return eligible


def build_evidence_pack(
    pareto_analysis: Mapping[str, Any],
    sensitivity_analysis: Mapping[str, Any] | None = None,
    constraints: AdvisorConstraints | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimized, auditable input pack without raw customer data."""
    current_constraints = _coerce_constraints(constraints)
    catalog = _candidate_catalog(pareto_analysis)
    evidence = {
        "objectives": dict(pareto_analysis.get("objectives", {})),
        "tiers": list(pareto_analysis.get("tiers", [])),
        "candidate_catalog": catalog,
        "constraints": {
            "max_mean_wait": current_constraints.max_mean_wait,
            "max_server_cost": current_constraints.max_server_cost,
            "require_sla_compliance": current_constraints.require_sla_compliance,
        },
        "sensitivity_baseline": (sensitivity_analysis or {}).get("baseline"),
        "sensitivity_rows": (sensitivity_analysis or {}).get("results", [])[:12],
    }
    evidence["evidence_fingerprint"] = _canonical_fingerprint(evidence)
    return evidence


def _deterministic_choice(evidence: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    constraints = _coerce_constraints(evidence["constraints"])
    eligible = _eligible_candidates(evidence["candidate_catalog"], constraints)
    if eligible:
        return min(eligible, key=lambda item: (item["server_cost"], item["mean_wait"], item["p95_wait"])), "least_cost_eligible_candidate"
    catalog = list(evidence["candidate_catalog"])
    return min(catalog, key=lambda item: (item["mean_wait"], item["p95_wait"], item["server_cost"])), "no_candidate_met_all_constraints"


def _build_proposal(
    *,
    evidence: Mapping[str, Any],
    selected: Mapping[str, Any],
    rationale: str,
    risks: Sequence[str],
    verification_steps: Sequence[str],
    confidence: str,
    execution_mode: str,
) -> dict[str, Any]:
    catalog_ids = {item["candidate_id"] for item in evidence["candidate_catalog"]}
    if selected["candidate_id"] not in catalog_ids:
        raise ValueError("selected candidate must come from the evidence catalog")
    return {
        "version": "v4.0-draft",
        "execution_mode": execution_mode,
        "evidence_fingerprint": evidence["evidence_fingerprint"],
        "selected_candidate": dict(selected),
        "rationale": rationale.strip(),
        "risks": [str(item).strip() for item in risks if str(item).strip()][:5],
        "verification_steps": [str(item).strip() for item in verification_steps if str(item).strip()][:6],
        "confidence": confidence if confidence in {"low", "medium", "high"} else "low",
        "approval_required": True,
        "applied": False,
        "external_operations_performed": False,
        "next_action": "A designated operator must review the evidence, re-run the simulation, and explicitly approve any operational change.",
    }


def create_deterministic_proposal(
    pareto_analysis: Mapping[str, Any],
    sensitivity_analysis: Mapping[str, Any] | None = None,
    constraints: AdvisorConstraints | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a non-LLM fallback proposal that is safe for tests and offline use."""
    evidence = build_evidence_pack(pareto_analysis, sensitivity_analysis, constraints)
    selected, reason = _deterministic_choice(evidence)
    if reason == "least_cost_eligible_candidate":
        rationale = (
            "Selected the lowest-cost candidate that satisfies the configured deterministic constraints. "
            "This is a draft recommendation, not an applied operational change."
        )
        risks = ["Demand and service-time uncertainty can change expected wait.", "Validate the plan with a fresh Monte Carlo run before approval."]
        confidence = "medium"
    else:
        rationale = (
            "No evaluated candidate met every configured constraint. Selected the candidate with the lowest modeled wait "
            "as an escalation draft; operator review is required."
        )
        risks = ["Configured constraint set is infeasible for the evaluated catalog.", "Do not apply capacity changes without revising constraints or generating additional candidates."]
        confidence = "low"
    return _build_proposal(
        evidence=evidence,
        selected=selected,
        rationale=rationale,
        risks=risks,
        verification_steps=[
            "Review the evidence fingerprint and candidate catalog.",
            "Re-run Monte Carlo with an approved replication count and current data.",
            "Confirm SLA, budget, and operator approval before any change.",
        ],
        confidence=confidence,
        execution_mode="deterministic-offline",
    )


def _llm_schema() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "queuecraft_capacity_advice",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "string"},
                    "rationale": {"type": "string"},
                    "risks": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                    "verification_steps": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["candidate_id", "rationale", "risks", "verification_steps", "confidence"],
                "additionalProperties": False,
            },
        },
    }


def create_generative_proposal(
    pareto_analysis: Mapping[str, Any],
    sensitivity_analysis: Mapping[str, Any] | None = None,
    constraints: AdvisorConstraints | Mapping[str, Any] | None = None,
    *,
    enable_llm: bool = False,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Generate an explanation over evaluated plans when explicitly enabled.

    The LLM selects only a candidate ID from the programmatically generated
    catalog. No LLM output can call a tool, mutate a scenario, or apply a plan.
    """
    if not enable_llm:
        return create_deterministic_proposal(pareto_analysis, sensitivity_analysis, constraints)
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("enable_llm=True requires an OpenAI-compatible API key in the environment")
    evidence = build_evidence_pack(pareto_analysis, sensitivity_analysis, constraints)
    # Lazy import keeps the offline desktop package usable without a model call.
    from openai import OpenAI

    system_prompt = (
        "You are QueueCraft's constrained capacity-analysis advisor. Choose exactly one candidate_id from the supplied catalog. "
        "Do not invent metrics, candidate IDs, data, or operational results. Do not instruct automated execution. "
        "Explain trade-offs, state uncertainty, and require human approval. Return JSON matching the schema."
    )
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(evidence, ensure_ascii=False)},
        ],
        response_format=_llm_schema(),
        max_completion_tokens=1200,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("generative advisor returned no structured content")
    generated = json.loads(content)
    catalog = {item["candidate_id"]: item for item in evidence["candidate_catalog"]}
    candidate_id = generated["candidate_id"]
    if candidate_id not in catalog:
        raise ValueError("generative advisor selected a candidate outside the verified catalog")
    return _build_proposal(
        evidence=evidence,
        selected=catalog[candidate_id],
        rationale=generated["rationale"],
        risks=generated["risks"],
        verification_steps=generated["verification_steps"],
        confidence=generated["confidence"],
        execution_mode=f"llm-structured:{model}",
    )
