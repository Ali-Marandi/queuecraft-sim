import tempfile, unittest
from pathlib import Path
from workspace_registry import WorkspaceRegistry
from rbac import Principal, authorize
from encrypted_store import EncryptedJsonStore
from worker_executor import BoundedWorker
from report_export import export_csv, build_manifest
from api_contract import response, require_fields
from enterprise_health import readiness_snapshot

class EnterpriseExpansionV2Tests(unittest.TestCase):
    def test_workspace_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg=WorkspaceRegistry(tmp); item=reg.create('ops-eu','EU Ops','alice')
            self.assertEqual(item['workspace_id'],'ops-eu'); self.assertEqual(len(reg.list()),1)
    def test_rbac_is_scoped_and_deny_by_default(self):
        analyst=Principal('alice','analyst')
        self.assertTrue(authorize(analyst,'decision:run')['allowed'])
        self.assertFalse(authorize(analyst,'scenario:delete',resource_owner_id='bob')['allowed'])
    def test_encrypted_store_roundtrip_and_wrong_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'workspace.enc'; EncryptedJsonStore(path,'correct-secret').write({'decision':11})
            self.assertEqual(EncryptedJsonStore(path,'correct-secret').read()['decision'],11)
            with self.assertRaises(ValueError): EncryptedJsonStore(path,'wrong-secret').read()
    def test_worker_execution(self):
        worker=BoundedWorker(1)
        try:
            result=worker.submit(lambda x:x*2,21).result(timeout=2)
            self.assertEqual(result.status,'completed'); self.assertEqual(result.value,42)
        finally: worker.shutdown()
    def test_reporting_and_contract(self):
        self.assertIn('capacity',export_csv([{'capacity':11,'sla':True}]))
        self.assertTrue(response(True,data={'x':1})['ok']); require_fields({'x':1},['x'])
        manifest=build_manifest(artifact_type='decision-json',content='{}',source_fingerprint='abc')
        self.assertEqual(len(manifest['content_sha256']),64)
    def test_health(self):
        out=readiness_snapshot(security_ok=True,rbac_ok=True,encrypted_store_ok=True,replay_ok=True,lineage_ok=True,policy_ok=True,worker_ok=True)
        self.assertEqual(out['status'],'ready_for_review'); self.assertFalse(out['certified'])

if __name__=='__main__': unittest.main()
