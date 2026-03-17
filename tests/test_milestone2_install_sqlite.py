import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from opsr.models.install import InstallRequest, InstallResult
from opsr.repositories.install_sqlite_repository import SqliteInstallResultRepository


class MilestoneTwoSqliteRepoTests(unittest.TestCase):
    def test_persists_and_reads_results(self) -> None:
        tmp_dir = Path(__file__).resolve().parent / ".tmp"
        tmp_dir.mkdir(exist_ok=True)
        db_path = tmp_dir / "install_repo.db"
        repo = SqliteInstallResultRepository(str(db_path))
        request = InstallRequest(component="mysql", target_host="10.0.0.9", config={"version": "8.0"})
        result = InstallResult(request=request, status="success")
        repo.add(result)

        results = repo.list_results()
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].request.component, "mysql")


if __name__ == "__main__":
    unittest.main()
