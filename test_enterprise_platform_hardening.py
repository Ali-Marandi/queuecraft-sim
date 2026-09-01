import unittest

from scenario_compiler import compile_scenario, verify_compiled_scenario
from signed_evidence import generate_keypair, sign_artifact, verify_signature
from simulation_performance import PerformancePolicy, choose_execution_mode, deterministic_replication_seeds, estimate_workload
from tenant_isolation import TenantContext, authorize_tenant, require_tenant_match, scoped_resource_id, tag_resource


class EnterprisePlatformHardeningTests(unittest.TestCase):
    def setUp(self):
        self.scenario = {
            "name": "capacity-check",
            "historical_counts": [8, 11, 13, 19, 22, 24, 20, 18],
            "tiers": [
                {"name": "triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
                {"name": "consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
            ],
            "simulation": {"horizon": 5, "replications": 100, "seed": 42},
        }

    def test_scenario_compiler_is_verifiable(self):
        compiled = compile_scenario(self.scenario)
        self.assertTrue(compiled["compiled"])
        self.assertEqual(compiled["plan"]["execution_class"], "interactive")
        self.assertTrue(verify_compiled_scenario(compiled)["valid"])
        compiled["scenario"]["tiers"][0]["servers"] = 3
        self.assertFalse(verify_compiled_scenario(compiled)["valid"])

    def test_signed_evidence_detects_tampering(self):
        private, public = generate_keypair()
        artifact = {"decision_id": "d1", "score": 0.92}
        envelope = sign_artifact(artifact, signer_id="governance-service", private_key_pem=private)
        self.assertTrue(verify_signature(artifact, envelope, public_key_pem=public)["valid"])
        artifact["score"] = 0.12
        self.assertFalse(verify_signature(artifact, envelope, public_key_pem=public)["valid"])

    def test_tenant_scope_is_explicit(self):
        context = TenantContext("tenant-a", "user-1", frozenset({"analyst"}))
        resource = tag_resource({"resource_id": "r1"}, context)
        self.assertTrue(authorize_tenant(context, resource)["allowed"])
        self.assertEqual(scoped_resource_id("tenant-a", "r1"), "tenant:tenant-a:resource:r1")
        with self.assertRaises(PermissionError):
            require_tenant_match(context, {"tenant_id": "tenant-b", "resource_id": "r1"})

    def test_performance_selection_and_seed_identity(self):
        workload = estimate_workload(replications=1000, horizon=10, stages=2, chunk_size=25)
        self.assertEqual(workload["work_units"], 20_000)
        self.assertEqual(choose_execution_mode(20_000)["mode"], "batch")
        self.assertEqual(deterministic_replication_seeds(42, 4), [42, 43, 44, 45])
        self.assertEqual(choose_execution_mode(1_000_000, PerformancePolicy(max_workers=4))["recommended_workers"], 4)

    def test_tenant_tag_rejects_cross_tenant_overwrite(self):
        context = TenantContext("tenant-a", "user-1", frozenset({"admin"}))
        with self.assertRaises(PermissionError):
            tag_resource({"tenant_id": "tenant-b"}, context)


if __name__ == "__main__":
    unittest.main()
