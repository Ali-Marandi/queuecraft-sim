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
from streaming_drift import DriftThresholds, StreamingDriftMonitor
from decision_ledger import DecisionLedger

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
        self.streaming_drift_monitor = StreamingDriftMonitor()
        self.decision_ledger = DecisionLedger()

    @staticmethod
    def _decode_payload(payload_json: str) -> dict[str, Any]:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("Request payload must be a JSON object")
        return payload

    def record_decision_event(self, payload_json: str) -> str:
        """Append one explicit local audit event to the decision ledger."""
        try:
            payload = self._decode_payload(payload_json)
            event_type = str(payload.get("event_type", "decision_observation"))
            event_payload = payload.get("payload", payload)
            if not isinstance(event_payload, dict):
                raise ValueError("event payload must be an object")
            return json.dumps(self.decision_ledger.append(event_type, event_payload), ensure_ascii=False)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def get_decision_ledger(self, limit: int = 200) -> str:
        """Return recent audit events plus the ledger integrity status."""
        try:
            return json.dumps({"events": self.decision_ledger.read(int(limit)), "integrity": self.decision_ledger.verify()})
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def verify_decision_ledger(self) -> str:
        """Verify the append-only hash chain without mutating it."""
        try:
            return json.dumps(self.decision_ledger.verify())
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def monitor_streaming_drift(self, payload_json: str) -> str:
        """Evaluate explicit local observations and report whether challenger evaluation is requested."""
        try:
            payload = self._decode_payload(payload_json)
            if "reference" in payload:
                thresholds = DriftThresholds(**{**self.streaming_drift_monitor.thresholds.__dict__, **payload.get("thresholds", {})})
                self.streaming_drift_monitor.thresholds = thresholds
                self.streaming_drift_monitor.seed_reference(payload["reference"])
            if "current" in payload:
                result = self.streaming_drift_monitor.ingest(payload["current"])
            else:
                result = self.streaming_drift_monitor.evaluate()
            if result.get("evaluation_requested"):
                self.decision_ledger.append("challenger_evaluation_requested", result)
            else:
                self.decision_ledger.append("drift_evaluation", result)
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def reset_streaming_drift(self) -> str:
        """Clear current drift window while retaining the reference distribution."""
        try:
            result = self.streaming_drift_monitor.reset_current()
            self.decision_ledger.append("drift_window_reset", result)
            return json.dumps(result)
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

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
            self.decision_ledger.append("simulation_completed", {"summary": result.get("summary", {}), "seed": payload.get("seed", 42)})
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
            self.decision_ledger.append("staffing_optimized", {"result": result.get("recommendation", result)})
            return json.dumps(result)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def save_scenario(self, payload_json: str) -> str:
        """Validate and save a reproducible local scenario with a fingerprint."""
        try:
            payload = self._decode_payload(payload_json)
            document = self.repository.save(payload.get("scenario", payload), payload.get("scenario_id"))
            self.decision_ledger.append("scenario_saved", {"scenario_id": document.get("id"), "fingerprint": document.get("fingerprint")})
            return json.dumps(document)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def get_live_slo_dashboard(self, history_limit: int = 60) -> str:
        try:
            return json.dumps(self.live_slo_monitor.dashboard_snapshot(history_limit=int(history_limit)))
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def advance_live_slo_demo(self) -> str:
        try:
            result = self.live_slo_monitor.advance_demo()
            self.decision_ledger.append("slo_observation", result)
            return json.dumps(result)
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def reset_live_slo_dashboard(self) -> str:
        try:
            result = self.live_slo_monitor.reset()
            self.decision_ledger.append("slo_dashboard_reset", result)
            return json.dumps(result)
        except (TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def list_scenarios(self) -> str:
        try:
            return json.dumps(self.repository.list())
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def load_scenario(self, scenario_id: str) -> str:
        try:
            return json.dumps(self.repository.load(scenario_id))
        except (FileNotFoundError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def delete_scenario(self, scenario_id: str) -> str:
        try:
            self.repository.delete(scenario_id)
            self.decision_ledger.append("scenario_deleted", {"scenario_id": scenario_id})
            return json.dumps({"deleted": True, "id": scenario_id})
        except (FileNotFoundError, TypeError, ValueError) as error:
            return json.dumps({"error": str(error)})

    def export_scenario_report(self, scenario_id: str) -> str:
        try:
            document = self.repository.load(scenario_id)
            scenario = document["scenario"]
            simulation = run_ai_monte_carlo(
                scenario["historical_counts"], scenario["tiers"],
                horizon=scenario["simulation"]["horizon"],
                replications=scenario["simulation"]["replications"],
                seed=scenario["simulation"]["seed"],
            )
            result = {
                "product": "QueueCraft Enterprise AI",
                "report_version": "1.0",
                "generated_at": document["updated_at"],
                "scenario": document,
                "simulation": simulation,
                "sla": evaluate_sla(simulation, scenario["sla"]["max_end_to_end_mean_wait"]),
            }
            self.decision_ledger.append("scenario_report_exported", {"scenario_id": scenario_id, "fingerprint": document.get("fingerprint")})
            return json.dumps(result)
        except (FileNotFoundError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            return json.dumps({"error": str(error)})

    def run_saved_scenario(self, scenario_id: str) -> str:
        try:
            document = self.repository.load(scenario_id)
            scenario = document["scenario"]
            simulation = run_ai_monte_carlo(
                scenario["historical_counts"], scenario["tiers"],
                horizon=scenario["simulation"]["horizon"],
                replications=scenario["simulation"]["replications"],
                seed=scenario["simulation"]["seed"],
            )
            result = {
                "scenario": {"id": document["id"], "name": scenario["name"], "fingerprint": document["fingerprint"]},
                "simulation": simulation,
                "sla": evaluate_sla(simulation, scenario["sla"]["max_end_to_end_mean_wait"]),
            }
            self.decision_ledger.append("scenario_executed", {"scenario_id": scenario_id, "fingerprint": document.get("fingerprint"), "sla": result["sla"]})
            return json.dumps(result)
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
        "QueueCraft Enterprise AI v3.11 — Decision Intelligence",
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
