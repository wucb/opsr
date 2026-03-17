from __future__ import annotations

from opsr.agents.install_agent import InstallAgent
from opsr.models.install import InstallRequest, InstallResult, InstallTemplate
from opsr.repositories.install_repository import InMemoryInstallTemplateRepository
from opsr.repositories.install_sqlite_repository import SqliteInstallResultRepository


class InstallOrchestrationService:
    """Milestone 2.2: database and middleware installation orchestration."""

    def __init__(
        self,
        template_repository: InMemoryInstallTemplateRepository | None = None,
        result_repository: SqliteInstallResultRepository | None = None,
        agent: InstallAgent | None = None,
    ) -> None:
        self.template_repository = template_repository or InMemoryInstallTemplateRepository()
        self.result_repository = result_repository or SqliteInstallResultRepository()
        self.agent = agent or InstallAgent()

    def list_templates(self, kind: str | None = None) -> list[InstallTemplate]:
        return self.template_repository.list_templates(kind)

    def submit_install(self, request: InstallRequest) -> InstallResult:
        template = self.template_repository.get_template(request.component)
        if template is None:
            result = InstallResult(
                request=request,
                status="failed",
                errors=[f"unknown component {request.component}"],
            )
            self.result_repository.add(result)
            return result

        merged_request = InstallRequest(
            component=request.component,
            target_host=request.target_host,
            config={**template.default_config, **request.config},
            requested_by=request.requested_by,
            requested_at=request.requested_at,
        )

        errors = self.agent.validate_request(template, merged_request)
        if errors:
            result = InstallResult(request=merged_request, status="failed", errors=errors)
            self.result_repository.add(result)
            return result

        plan = self.agent.build_plan(merged_request)
        result = self.agent.execute_plan(merged_request, plan)
        self.result_repository.add(result)
        return result

    def list_results(self) -> list[InstallResult]:
        return self.result_repository.list_results()
