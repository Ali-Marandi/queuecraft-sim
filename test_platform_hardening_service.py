import json
import unittest

from platform_hardening_service import (
    compile_scenario_json,
    performance_plan_json,
    tenant_scope_json,
    verify_compiled_scenario_json,
)
from signed_evidence import generate_keypair, sign_artifact
from platform_hardening_service import verify_signature_json


class PlatformHardeningServiceTests(unittest.TestCase):
    def setUp(self):
        self.scenario = {
            "historical_counts": [10, 12, 13, 15, 18, 20],
            "tiers": [{"name": "service", "servers": 2, "mean_service_time": 0.5, "service_cv": 1.0}],
            "simulation": {"horizon": 4, "replications": 100, "seed": 7},
        }

    def test_compile_and_verify_json_contract(self):
        compiled = json.loads(compile_scenario_json(json.dumps(self.scenario)))
        self.assertTrue(compiled["compiled"])
        verified = json.loads(verify_compiled_scenario_json(json.dumps(compiled)))
        self.assertTrue(verified["valid"])

    def test_performance_contract(self):
        result = json.loads(performance_plan_json(replications=1000, horizon=10, stages=2, chunk_size=20))
        self.assertEqual(result["execution"]["mode"], "batch")
        self.assertGreater(result["workload"]["chunks"], 1)

    def test_tenant_contract(self):
        result = json.loads(tenant_scope_json(tenant_id="a", principal_id="u1", roles=["analyst"], resource_id="r1"))
        self.assertTrue(result["authorization"]["allowed"])
        denied = json.loads(tenant_scope_json(tenant_id="a", principal_id="u1", roles=["analyst"], resource_id="r1", resource_tenant_id="b"))
        self.assertFalse(denied["authorization"]["allowed"])

    def test_signature_service_contract(self):
        private, public = generate_keypair()
        artifact = {"decision_id": "d1", "score": 0.9}
        envelope = sign_artifact(artifact, signer_id="svc", private_key_pem=private)
        result = json.loads(verify_signature_json(json.dumps(artifact), json.dumps(envelope), public_key_pem=public))
        self.assertTrue(result["valid"])


if __name__ == "__main__":
    unittest.main()
