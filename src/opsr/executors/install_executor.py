from __future__ import annotations

from dataclasses import dataclass

from opsr.models.install import InstallRequest


@dataclass(slots=True)
class StepExecutionResult:
    step: str
    status: str
    message: str


class InstallExecutor:
    """Abstract executor for install steps."""

    def run_step(self, request: InstallRequest, step: str) -> StepExecutionResult:  # pragma: no cover
        raise NotImplementedError


class SimulatedInstallExecutor(InstallExecutor):
    """Simulates install steps for milestone 2.2."""

    def run_step(self, request: InstallRequest, step: str) -> StepExecutionResult:
        simulate_failure = request.config.get("simulate_failure")
        if simulate_failure == step:
            return StepExecutionResult(step=step, status="failed", message=f"{step} failed by simulation")
        return StepExecutionResult(step=step, status="success", message=f"{step} completed")


class SshInstallExecutor(InstallExecutor):
    """Placeholder for SSH-based execution."""

    def run_step(self, request: InstallRequest, step: str) -> StepExecutionResult:
        return StepExecutionResult(
            step=step,
            status="failed",
            message="ssh executor not configured",
        )