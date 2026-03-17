from __future__ import annotations

from opsr.models.install import InstallResult, InstallTemplate


class InMemoryInstallTemplateRepository:
    """In-memory catalog for install templates."""

    def __init__(self) -> None:
        self._templates: dict[str, InstallTemplate] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        defaults = [
            InstallTemplate(
                component="mysql",
                kind="database",
                supported_versions=["8.0", "5.7"],
                required_config_keys=["data_dir", "admin_user"],
                default_config={"port": 3306, "resources": {"cpu_cores": 2, "memory_gb": 4}},
            ),
            InstallTemplate(
                component="postgres",
                kind="database",
                supported_versions=["16", "15"],
                required_config_keys=["data_dir", "admin_user"],
                default_config={"port": 5432, "resources": {"cpu_cores": 2, "memory_gb": 4}},
            ),
            InstallTemplate(
                component="redis",
                kind="middleware",
                supported_versions=["7", "6"],
                required_config_keys=["data_dir"],
                default_config={"port": 6379, "resources": {"cpu_cores": 1, "memory_gb": 2}},
            ),
            InstallTemplate(
                component="mongodb",
                kind="database",
                supported_versions=["7.0", "6.0"],
                required_config_keys=["data_dir", "admin_user"],
                default_config={"port": 27017, "resources": {"cpu_cores": 2, "memory_gb": 4}},
            ),
            InstallTemplate(
                component="kafka",
                kind="middleware",
                supported_versions=["3.6", "3.5"],
                required_config_keys=["data_dir", "zookeeper_connect"],
                default_config={"port": 9092, "resources": {"cpu_cores": 4, "memory_gb": 8}},
            ),
            InstallTemplate(
                component="rabbitmq",
                kind="middleware",
                supported_versions=["3.13", "3.12"],
                required_config_keys=["data_dir", "admin_user"],
                default_config={"port": 5672, "resources": {"cpu_cores": 2, "memory_gb": 4}},
            ),
            InstallTemplate(
                component="nginx",
                kind="middleware",
                supported_versions=["1.24", "1.22"],
                required_config_keys=["config_path"],
                default_config={"port": 80, "resources": {"cpu_cores": 1, "memory_gb": 1}},
            ),
        ]
        for template in defaults:
            self._templates[template.component] = template

    def list_templates(self, kind: str | None = None) -> list[InstallTemplate]:
        templates = list(self._templates.values())
        if kind:
            return [template for template in templates if template.kind == kind]
        return templates

    def get_template(self, component: str) -> InstallTemplate | None:
        return self._templates.get(component)


class InMemoryInstallResultRepository:
    """Store install runs for auditing in memory."""

    def __init__(self) -> None:
        self._results: list[InstallResult] = []

    def add(self, result: InstallResult) -> None:
        self._results.append(result)

    def list_results(self) -> list[InstallResult]:
        return list(self._results)
