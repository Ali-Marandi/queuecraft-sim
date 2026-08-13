"""Safe distributed stress scenarios for QueueCraft.

Every scenario runs the local capacity model only. The module does not perform
HTTP, socket, cloud-provider, or external load-generation operations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from distributed_load_testing import DistributedLoadPolicy, LoadGenerator, TargetRegion, simulate_distributed_load


BASE_GENERATORS = [
    LoadGenerator("americas-client", max_requests_per_bucket=240, routing_weight=2.0),
    LoadGenerator("europe-client", max_requests_per_bucket=200, routing_weight=1.5),
    LoadGenerator("asia-client", max_requests_per_bucket=180, routing_weight=1.0),
]
BASE_TARGETS = [
    TargetRegion("americas-region", capacity_per_bucket=220, service_latency_ms=30),
    TargetRegion("europe-region", capacity_per_bucket=180, service_latency_ms=35),
    TargetRegion("asia-region", capacity_per_bucket=160, service_latency_ms=40),
]
BASE_LATENCY = {
    "americas-client": {"americas-region": 20, "europe-region": 100, "asia-region": 180},
    "europe-client": {"americas-region": 100, "europe-region": 20, "asia-region": 130},
    "asia-client": {"americas-region": 180, "europe-region": 130, "asia-region": 25},
}


def _scenario_definitions() -> dict[str, dict[str, Any]]:
    return {
        "global_peak": {
            "description": "Heavy global demand without a regional outage.",
            "load": [180, 240, 300, 360, 400, 360, 300],
            "generators": BASE_GENERATORS,
            "targets": BASE_TARGETS,
            "latency": BASE_LATENCY,
            "policy": DistributedLoadPolicy(routing_mode="latency_aware", saturation_penalty_ms=12, latency_slo_ms=250),
            "outages": {},
            "acceptance": {"minimum_served_pct": 99.0, "maximum_p95_latency_ms": 250.0, "maximum_unserved_requests": 4},
            "expected_outcome": "pass",
        },
        "regional_outage_peak": {
            "description": "Europe region is unavailable at the global peak; test failover capacity and latency.",
            "load": [180, 240, 300, 360, 360, 300, 240],
            "generators": BASE_GENERATORS,
            "targets": BASE_TARGETS,
            "latency": BASE_LATENCY,
            "policy": DistributedLoadPolicy(routing_mode="latency_aware", saturation_penalty_ms=12, latency_slo_ms=400),
            "outages": {3: {"europe-region"}},
            "acceptance": {"minimum_served_pct": 88.0, "maximum_p95_latency_ms": 400.0, "maximum_unserved_requests": 100},
            "expected_outcome": "pass",
        },
        "generator_constrained": {
            "description": "The model asks for more demand than the configured source generators can produce.",
            "load": [500, 540, 580, 600],
            "generators": [
                LoadGenerator("americas-client", max_requests_per_bucket=90, routing_weight=2.0),
                LoadGenerator("europe-client", max_requests_per_bucket=70, routing_weight=1.5),
                LoadGenerator("asia-client", max_requests_per_bucket=50, routing_weight=1.0),
            ],
            "targets": BASE_TARGETS,
            "latency": BASE_LATENCY,
            "policy": DistributedLoadPolicy(routing_mode="latency_aware", saturation_penalty_ms=10, latency_slo_ms=250),
            "outages": {},
            "acceptance": {"minimum_served_pct": 99.0, "maximum_p95_latency_ms": 250.0, "maximum_unserved_requests": 0, "minimum_generator_limited_requests": 1},
            "expected_outcome": "pass",
        },
        "sustained_saturation": {
            "description": "Persistent demand exceeds the combined regional capacity to verify explicit rejection metrics.",
            "load": [600, 620, 640, 660, 680, 660],
            "generators": BASE_GENERATORS,
            "targets": BASE_TARGETS,
            "latency": BASE_LATENCY,
            "policy": DistributedLoadPolicy(routing_mode="latency_aware", saturation_penalty_ms=25, latency_slo_ms=250),
            "outages": {},
            "acceptance": {"minimum_served_pct": 99.0, "maximum_p95_latency_ms": 250.0, "maximum_unserved_requests": 0},
            "expected_outcome": "fail",
        },
        "latency_partition": {
            "description": "Cross-region paths become slow without a full regional outage.",
            "load": [230, 270, 320, 360, 320, 270],
            "generators": BASE_GENERATORS,
            "targets": BASE_TARGETS,
            "latency": {
                "americas-client": {"americas-region": 20, "europe-region": 260, "asia-region": 360},
                "europe-client": {"americas-region": 260, "europe-region": 20, "asia-region": 280},
                "asia-client": {"americas-region": 360, "europe-region": 280, "asia-region": 25},
            },
            "policy": DistributedLoadPolicy(routing_mode="latency_aware", saturation_penalty_ms=15, latency_slo_ms=230),
            "outages": {},
            "acceptance": {"minimum_served_pct": 99.0, "maximum_p95_latency_ms": 230.0, "maximum_unserved_requests": 0},
            "expected_outcome": "pass",
        },
    }


def evaluate_acceptance(summary: dict[str, Any], acceptance: dict[str, float]) -> dict[str, Any]:
    checks = {
        "served_pct": summary["served_pct_of_generated"] >= acceptance["minimum_served_pct"],
        "unserved_requests": summary["total_unserved_requests"] <= acceptance["maximum_unserved_requests"],
        "p95_latency": (
            summary["global_p95_estimated_latency_ms"] is not None
            and summary["global_p95_estimated_latency_ms"] <= acceptance["maximum_p95_latency_ms"]
        ),
    }
    if "minimum_generator_limited_requests" in acceptance:
        checks["generator_limited"] = (
            summary["generator_capacity_limited_requests"] >= acceptance["minimum_generator_limited_requests"]
        )
    return {"passed": all(checks.values()), "checks": checks, "criteria": acceptance}


def run_scenario(name: str) -> dict[str, Any]:
    scenarios = _scenario_definitions()
    if name not in scenarios:
        raise ValueError(f"unknown scenario '{name}'; choose one of: {', '.join(sorted(scenarios))}")
    spec = scenarios[name]
    result = simulate_distributed_load(
        spec["load"], spec["generators"], spec["targets"], spec["latency"], spec["policy"], outages_by_bucket=spec["outages"]
    )
    acceptance = evaluate_acceptance(result["summary"], spec["acceptance"])
    expected = spec["expected_outcome"]
    return {
        "scenario": name,
        "description": spec["description"],
        "safe_mode": result["safe_mode"],
        "expected_outcome": expected,
        "acceptance": acceptance,
        "expectation_met": acceptance["passed"] == (expected == "pass"),
        "summary": result["summary"],
        "timeline": result["timeline"],
    }


def main() -> int:
    scenarios = _scenario_definitions()
    parser = argparse.ArgumentParser(description="Run QueueCraft local distributed stress scenarios; sends no network traffic.")
    parser.add_argument("--scenario", choices=["all", *sorted(scenarios)], default="all")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    parser.add_argument("--fail-on-expectation", action="store_true", help="Return exit code 1 if a scenario does not meet its expected pass/fail outcome.")
    args = parser.parse_args()
    names = sorted(scenarios) if args.scenario == "all" else [args.scenario]
    reports = [run_scenario(name) for name in names]
    payload = {"safe_mode": {"network_requests_sent": 0}, "reports": reports}
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    failed_expectations = [report["scenario"] for report in reports if not report["expectation_met"]]
    if args.fail_on_expectation and failed_expectations:
        print(f"Scenario expectation mismatch: {', '.join(failed_expectations)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
