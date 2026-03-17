import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.models.install import InstallRequest
from opsr.repositories.install_sqlite_repository import SqliteInstallResultRepository
from opsr.services.install_service import InstallOrchestrationService


class MilestoneTwoInstallTests(unittest.TestCase):
    def _db_path(self) -> str:
        tmp_dir = Path(__file__).resolve().parent / ".tmp"
        tmp_dir.mkdir(exist_ok=True)
        return str(tmp_dir / "install.db")

    def test_template_catalog_includes_mysql(self) -> None:
        service = InstallOrchestrationService(
            result_repository=SqliteInstallResultRepository(self._db_path())
        )
        components = {template.component for template in service.list_templates()}
        self.assertIn("mysql", components)

    def test_invalid_version_rejected(self) -> None:
        service = InstallOrchestrationService(
            result_repository=SqliteInstallResultRepository(self._db_path())
        )
        result = service.submit_install(
            InstallRequest(
                component="postgres",
                target_host="10.0.0.10",
                config={
                    "version": "12",
                    "data_dir": "/data/postgres",
                    "admin_user": "postgres",
                },
            )
        )
        self.assertEqual(result.status, "failed")
        self.assertTrue(any("not supported" in error for error in result.errors))

    def test_successful_install_uses_defaults(self) -> None:
        service = InstallOrchestrationService(
            result_repository=SqliteInstallResultRepository(self._db_path())
        )
        result = service.submit_install(
            InstallRequest(
                component="redis",
                target_host="10.0.0.11",
                config={
                    "version": "7",
                    "data_dir": "/data/redis",
                },
            )
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(result.request.config["port"], 6379)
        self.assertTrue(any(step.step == "health_check" for step in result.steps))

    def test_failure_triggers_rollback(self) -> None:
        service = InstallOrchestrationService(
            result_repository=SqliteInstallResultRepository(self._db_path())
        )
        result = service.submit_install(
            InstallRequest(
                component="mysql",
                target_host="10.0.0.12",
                config={
                    "version": "8.0",
                    "data_dir": "/data/mysql",
                    "admin_user": "root",
                    "simulate_failure": "configure",
                },
            )
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.steps[-1].step, "rollback")


if __name__ == "__main__":
    unittest.main()
