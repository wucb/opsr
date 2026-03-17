from __future__ import annotations

from datetime import datetime, timezone

from opsr.executors.install_executor import InstallExecutor, SimulatedInstallExecutor
from opsr.models.install import InstallRequest, InstallResult, InstallStepResult, InstallTemplate


class InstallAgent:
    """Agent that validates install requests and simulates orchestration."""

    DEFAULT_PLAN = ["prepare", "install", "configure", "initialize", "health_check"]

    def __init__(self, executor: InstallExecutor | None = None) -> None:
        self.executor = executor or SimulatedInstallExecutor()

    def validate_request(self, template: InstallTemplate, request: InstallRequest) -> list[str]:
        errors: list[str] = []
        config = {**template.default_config, **request.config}

        version = config.get("version")
        if version is None:
            errors.append("config.version is required")
        elif version not in template.supported_versions:
            errors.append(f"version {version} is not supported for {template.component}")

        for key in template.required_config_keys:
            if key not in config:
                errors.append(f"config.{key} is required")

        port = config.get("port")
        if port is not None:
            if not isinstance(port, int) or port <= 0 or port > 65535:
                errors.append("config.port must be a valid TCP port (1-65535)")

        resources = config.get("resources")
        if resources is not None:
            cpu = resources.get("cpu_cores")
            memory = resources.get("memory_gb")
            if cpu is None or memory is None:
                errors.append("config.resources must include cpu_cores and memory_gb")
            elif cpu <= 0 or memory <= 0:
                errors.append("config.resources cpu_cores and memory_gb must be positive")

        return errors

    def build_plan(self, request: InstallRequest) -> list[str]:
        plan = list(self.DEFAULT_PLAN)
        if request.config.get("skip_initialize"):
            plan.remove("initialize")
        return plan

    def execute_plan(self, request: InstallRequest, plan: list[str]) -> InstallResult:
        steps: list[InstallStepResult] = []
        errors: list[str] = []
        for step in plan:
            started_at = datetime.now(timezone.utc)
            execution = self.executor.run_step(request, step)
            status = execution.status
            message = execution.message
            if status == "failed":
                errors.append(message)
            finished_at = datetime.now(timezone.utc)
            steps.append(
                InstallStepResult(
                    step=step,
                    status=status,
                    message=message,
                    started_at=started_at,
                    finished_at=finished_at,
                )
            )
            if status == "failed":
                break

        if errors:
            steps.append(
                InstallStepResult(
                    step="rollback",
                    status="success",
                    message="rollback completed",
                    started_at=datetime.now(timezone.utc),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            return InstallResult(
                request=request,
                status="failed",
                steps=steps,
                errors=errors,
                completed_at=datetime.now(timezone.utc),
            )

        return InstallResult(
            request=request,
            status="success",
            steps=steps,
            completed_at=datetime.now(timezone.utc),
        )
