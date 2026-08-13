"""QueueCraft Enterprise AI desktop entry point and local Python API bridge."""

import http.server
import json
import os
import socketserver
import sys
import threading
from typing import Any

import webview

from ai_monte_carlo import forecast_arrival_rates, optimize_staffing, run_ai_monte_carlo
from data_import import DataImportError, import_arrival_data
from decision_analytics import capacity_pareto_analysis, sensitivity_analysis
from cloud_cluster_scaling import ClusterPolicy, forecast_cluster_scaling, simulate_cluster_scaling
from multi_region_failover import FailoverPolicy, RegionConfig, SLODefinition, simulate_multi_region_failover
from distributed_load_testing import DistributedLoadPolicy, LoadGenerator, TargetRegion, simulate_distributed_load
from live_slo_monitoring import LiveSLOMonitor
from generative_queue_optimizer import create_generative_proposal
from scenario_manager import ScenarioRepository, evaluate_sla

PORT = 8765


def resource_path(relative_path: str = "") -> str:
    """Resolve files in development and within a PyInstaller one-file bundle."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


DIRECTORY = resource_path()


class API:
    """Methods exposed safely to the browser UI through pywebview."""

    DEFAULT_HISTORY = [8, 11, 13, 19, 22, 24, 20, 18, 21, 27, 31, 34]
    DEFAULT_TIERS = [
        {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
        {"name": "Consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
    ]
    DEFAULT_REGIONS = [
        {"name": "region-a", "capacity_per_bucket": 40, "routing_weight": 2.0, "base_latency_ms": 45.0},
        {"name": "region-b", "capacity_per_bucket": 35, "routing_weight": 1.0, "base_latency_ms": 70.0},
    ]
    DEFAULT_FAILOVER_POLICY = {"mode": "active_active", "failover_latency_penalty_ms": 25.0}
    DEFAULT_SLO = {"availability_target": 0.99, "latency_threshold_ms": 250.0, "rolling_window_buckets": 30}
    DEFAULT_GLOBAL_LOAD_GENERATORS = [
        {"name": "americas-client", "max_requests_per_bucket": 120, "routing_weight": 2.0},
        {"name": "europe-client", "max_requests_per_bucket": 100, "routing_weight": 1.5},
        {"name": "asia-client", "max_requests_per_bucket": 100, "routing_weight": 1.0},
    ]
    DEFAULT_GLOBAL_TARGETS = [
        {"name": "americas-region", "capacity_per_bucket": 100, "service_latency_ms": 30.0},
        {"name": "europe-region", "capacity_per_bucket": 90, "service_latency_ms": 35.0},
        {"name": "asia-region", "capacity_per_bucket": 80, "service_latency_ms": 40.0},
    ]
    DEFAULT_GLOBAL_NETWORK_LATENCY = {
        "americas-client": {"americas-region": 20, "europe-region": 100, "asia-region": 180},
        "europe-client": {"americas-region": 100, "europe-region": 20, "asia-region": 130},
        "asia-client": {"americas-region": 180, "europe-region": 130, "asia-region": 25},
    }
    DEFAULT_GLOBAL_LOAD_POLICY = {"routing_mode": "latency_aware", "saturation_penalty_ms": 20.0, "latency_slo_ms": 250.0}
    DEFAULT_CLUSTER_POLICY = {
        "min_nodes": 2,
        "max_nodes": 12,
        "node_capacity": 20,
        "target_utilization": 0.70,
        "scale_up_step": 2,
        "scale_down_step": 1,
        "warmup_buckets": 1,
        "cooldown_buckets": 1,
        "per_node_cost_per_bucket": 1.0,
        "backlog_penalty_per_job": 0.10,
        "routing_strategy": "least_loaded",
    }

    def __init__(self) -> None:
        self.repository = ScenarioRepository()
        self.last_import: dict[str, Any] | None = None
        self.live_slo_monitor = LiveSLOMonitor(SLODefinition(**self.DEFAULT_SLO), max_history_points=120)

    @staticmethod
    def _decode_payload(payload_json: str) -> dict[str, Any]:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("Request payload must be a JSON object")
        return payload

    def select_arrival_file(self) -> str:
        """Open a native file picker; the user explicitly chooses local source data."""
        try:
            selected = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=("Queue data (*.csv;*.xlsx;*.xls)",),
            )
            if not selected:
                return json.dumps({"cancelled": True})
            return json.dumps({"cancelled": False, "path": selected[0]})
        except (IndexError, OSError, RuntimeError) as error:
            return json.dumps({"error": str(error)})

    def import_arrival_file(self, path: str, options_json: str = "") -> str:
        """Validate a selected CSV/XLSX file and retain only normalized arrival buckets."""
        try:
            options = self._decode_payload(options_json) if options_json else {}
            imported = import_arrival_data(path, options)
            self.last_import = imported.to_dict()
            return json.dumps(self.last_import)
        except (DataImportError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def forecast_load(self, arrivals_json: str) -> str:
        """Return short-horizon demand forecasting without running a simulation."""
        try:
            history = json.loads(arrivals_json) if arrivals_json else (self.last_import or {}).get("historical_counts", self.DEFAULT_HISTORY)
            if not isinstance(history, list) or len(history) < 5:
                history = self.DEFAULT_HISTORY
            return json.dumps(forecast_arrival_rates(history, horizon=5))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def run_ai_monte_carlo(self, payload_json: str) -> str:
        """Forecast demand and execute a multi-tier Monte Carlo risk analysis."""
        try:
            payload = self._decode_payload(payload_json)
            result = run_ai_monte_carlo(
                payload.get("historical_counts", self.DEFAULT_HISTORY),
                payload.get("tiers", self.DEFAULT_TIERS),
                horizon=int(payload.get("horizon", 5)),
                bucket_duration=float(payload.get("bucket_duration", 1.0)),
                replications=int(payload.get("replications", 500)),
                seed=payload.get("seed", 42),
            )
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def optimize_staffing(self, payload_json: str) -> str:
        """Return the lowest-cost server allocation satisfying the requested SLA."""
        try:
            payload = self._decode_payload(payload_json)
            result = optimize_staffing(
                payload.get("historical_counts", self.DEFAULT_HISTORY),
                payload.get("tiers", self.DEFAULT_TIERS),
                server_range=tuple(payload.get("server_range", [1, 6])),
                max_end_to_end_mean_wait=float(payload.get("max_end_to_end_mean_wait", 5.0)),
                cost_per_server=float(payload.get("cost_per_server", 1.0)),
                replications=int(payload.get("replications", 200)),
                seed=payload.get("seed", 42),
            )
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def ingest_live_slo_observation(self, payload_json: str) -> str:
        """Ingest an explicitly supplied local observation; no telemetry is sent externally."""
        try:
            return json.dumps(self.live_slo_monitor.ingest(self._decode_payload(payload_json)))
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def get_live_slo_dashboard(self, history_limit: int = 60) -> str:
        """Read the bounded in-memory SLO dashboard snapshot for the local desktop session."""
        try:
            return json.dumps(self.live_slo_monitor.dashboard_snapshot(history_limit=int(history_limit)))
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def advance_live_slo_demo(self) -> str:
        """Add one fixed illustrative local observation to the dashboard."""
        try:
            return json.dumps(self.live_slo_monitor.advance_demo())
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def reset_live_slo_dashboard(self) -> str:
        """Clear only the in-memory monitoring data for this desktop session."""
        try:
            return json.dumps(self.live_slo_monitor.reset())
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def run_distributed_load_test(self, payload_json: str) -> str:
        """Run a safe local capacity model; this method sends no network traffic."""
        try:
            payload = self._decode_payload(payload_json)
            requested = payload.get("global_load_buckets", (self.last_import or {}).get("historical_counts", self.DEFAULT_HISTORY))
            result = simulate_distributed_load(
                requested,
                [LoadGenerator(**generator) for generator in payload.get("load_generators", self.DEFAULT_GLOBAL_LOAD_GENERATORS)],
                [TargetRegion(**target) for target in payload.get("target_regions", self.DEFAULT_GLOBAL_TARGETS)],
                payload.get("network_latency_ms", self.DEFAULT_GLOBAL_NETWORK_LATENCY),
                DistributedLoadPolicy(**{**self.DEFAULT_GLOBAL_LOAD_POLICY, **payload.get("policy", {})}),
                outages_by_bucket=payload.get("outages_by_bucket", {}),
            )
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def run_multi_region_failover(self, payload_json: str) -> str:
        """Run a local multi-region resilience simulation without cloud mutations."""
        try:
            payload = self._decode_payload(payload_json)
            arrivals = payload.get("arrival_buckets", (self.last_import or {}).get("historical_counts", self.DEFAULT_HISTORY))
            regions = [RegionConfig(**region) for region in payload.get("regions", self.DEFAULT_REGIONS)]
            policy = FailoverPolicy(**{**self.DEFAULT_FAILOVER_POLICY, **payload.get("failover_policy", {})})
            slo = SLODefinition(**{**self.DEFAULT_SLO, **payload.get("slo_definition", {})})
            result = simulate_multi_region_failover(
                arrivals,
                regions,
                policy,
                slo,
                outages_by_bucket=payload.get("outages_by_bucket", {}),
            )
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def run_cluster_scaling(self, payload_json: str) -> str:
        """Simulate local cluster scaling; this method never calls a cloud provider."""
        try:
            payload = self._decode_payload(payload_json)
            history = payload.get("historical_counts", (self.last_import or {}).get("historical_counts", self.DEFAULT_HISTORY))
            policy = ClusterPolicy(**{**self.DEFAULT_CLUSTER_POLICY, **payload.get("cluster_policy", {})})
            forecast = forecast_cluster_scaling(history, policy, horizon=int(payload.get("horizon", 8)))
            arrivals = payload.get(
                "arrival_buckets",
                [int(round(item["forecast_arrivals"])) for item in forecast["pre_scaling_plan"]],
            )
            simulation = simulate_cluster_scaling(arrivals, policy, initial_nodes=payload.get("initial_nodes"))
            return json.dumps({"forecast": forecast, "simulation": simulation})
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def run_pareto_analysis(self, payload_json: str) -> str:
        """Evaluate non-dominated capacity plans on cost and queue-wait objectives."""
        try:
            payload = self._decode_payload(payload_json)
            result = capacity_pareto_analysis(
                payload.get("historical_counts", (self.last_import or {}).get("historical_counts", self.DEFAULT_HISTORY)),
                payload.get("tiers", self.DEFAULT_TIERS),
                server_range=tuple(payload.get("server_range", [1, 6])),
                cost_per_server=float(payload.get("cost_per_server", 1.0)),
                sla_mean_wait=payload.get("sla_mean_wait", 5.0),
                replications=int(payload.get("replications", 100)),
                seed=payload.get("seed", 42),
            )
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def create_v4_queue_proposal(self, payload_json: str) -> str:
        """Create an auditable capacity draft; LLM use remains opt-in and never applies a change."""
        try:
            payload = self._decode_payload(payload_json)
            history = payload.get("historical_counts", (self.last_import or {}).get("historical_counts", self.DEFAULT_HISTORY))
            tiers = payload.get("tiers", self.DEFAULT_TIERS)
            replications = int(payload.get("replications", 100))
            seed = payload.get("seed", 42)
            pareto = capacity_pareto_analysis(
                history,
                tiers,
                server_range=tuple(payload.get("server_range", [1, 6])),
                cost_per_server=float(payload.get("cost_per_server", 1.0)),
                sla_mean_wait=payload.get("sla_mean_wait", 5.0),
                replications=replications,
                seed=seed,
            )
            sensitivity = sensitivity_analysis(
                history,
                tiers,
                arrival_multipliers=payload.get("arrival_multipliers", [0.8, 1.0, 1.2]),
                service_time_multipliers=payload.get("service_time_multipliers", [0.8, 1.0, 1.2]),
                replications=replications,
                seed=seed,
            )
            proposal = create_generative_proposal(
                pareto,
                sensitivity,
                constraints=payload.get("constraints", {"require_sla_compliance": True}),
                enable_llm=bool(payload.get("enable_llm", False)),
                model=str(payload.get("model", "gpt-5-mini")),
            )
            return json.dumps({"proposal": proposal, "pareto_summary": {"recommendation": pareto["recommendation"], "candidate_count": pareto["candidates_evaluated"]}})
        except (TypeError, ValueError, KeyError, RuntimeError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def run_sensitivity_analysis(self, payload_json: str) -> str:
        """Evaluate queue exposure to demand and service-duration uncertainty."""
        try:
            payload = self._decode_payload(payload_json)
            result = sensitivity_analysis(
                payload.get("historical_counts", (self.last_import or {}).get("historical_counts", self.DEFAULT_HISTORY)),
                payload.get("tiers", self.DEFAULT_TIERS),
                arrival_multipliers=payload.get("arrival_multipliers", [0.8, 1.0, 1.2]),
                service_time_multipliers=payload.get("service_time_multipliers", [0.8, 1.0, 1.2]),
                replications=int(payload.get("replications", 100)),
                seed=payload.get("seed", 42),
            )
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def save_scenario(self, payload_json: str) -> str:
        """Validate and save a reproducible local scenario with a fingerprint."""
        try:
            payload = self._decode_payload(payload_json)
            document = self.repository.save(payload.get("scenario", payload), payload.get("scenario_id"))
            return json.dumps(document)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def list_scenarios(self) -> str:
        """List locally stored, integrity-verified scenario summaries."""
        try:
            return json.dumps(self.repository.list())
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def run_saved_scenario(self, scenario_id: str) -> str:
        """Run an auditable scenario and explicitly evaluate its configured SLA."""
        try:
            document = self.repository.load(scenario_id)
            scenario = document["scenario"]
            simulation = run_ai_monte_carlo(
                scenario["historical_counts"],
                scenario["tiers"],
                horizon=scenario["simulation"]["horizon"],
                replications=scenario["simulation"]["replications"],
                seed=scenario["simulation"]["seed"],
            )
            return json.dumps(
                {
                    "scenario": {
                        "id": document["id"],
                        "name": scenario["name"],
                        "fingerprint": document["fingerprint"],
                    },
                    "simulation": simulation,
                    "sla": evaluate_sla(simulation, scenario["sla"]["max_end_to_end_mean_wait"]),
                }
            )
        except (FileNotFoundError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        pass


class ReusableTcpServer(socketserver.TCPServer):
    allow_reuse_address = True


def start_server() -> None:
    with ReusableTcpServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()


def main() -> None:
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    window = webview.create_window(
        "QueueCraft Enterprise AI v3.2 — Global Resilience",
        f"http://127.0.0.1:{PORT}/index.html",
        js_api=API(),
        width=1366,
        height=850,
        resizable=True,
        min_width=900,
        min_height=650,
    )
    webview.start()


if __name__ == "__main__":
    main()
