from __future__ import annotations

import uuid

from opsr.models.assistant import AssistantAction, AssistantRequest, AssistantResponse, AssistantSuggestion
from opsr.services.install_service import InstallOrchestrationService
from opsr.services.runbook_service import RunbookService


class AssistantService:
    """Milestone 2.4: lightweight AI ops assistant (rule-based intent + approvals)."""

    def __init__(
        self,
        runbook_service: RunbookService | None = None,
        install_service: InstallOrchestrationService | None = None,
    ) -> None:
        self.runbook_service = runbook_service or RunbookService()
        self.install_service = install_service or InstallOrchestrationService()

    def triage(self, text: str, requested_by: str) -> AssistantResponse:
        request = AssistantRequest(text=text, requested_by=requested_by)
        suggestions: list[AssistantSuggestion] = []
        lowered = text.lower()

        runbook_suggestion = self._suggest_runbook(lowered)
        if runbook_suggestion:
            suggestions.append(runbook_suggestion)

        install_suggestion = self._suggest_install(lowered)
        if install_suggestion:
            suggestions.append(install_suggestion)

        if not suggestions:
            suggestions.append(
                AssistantSuggestion(
                    intent="unknown",
                    confidence=0.2,
                    notes=["No matching runbook or install template found."],
                )
            )

        return AssistantResponse(request=request, suggestions=suggestions)

    def request_runbook_approval(self, runbook_id: str, requested_by: str) -> dict[str, object]:
        approval = self.runbook_service.request_approval(runbook_id, requested_by)
        return approval.__dict__

    def execute_runbook(self, runbook_id: str, requested_by: str, approved_by: str | None) -> dict[str, object]:
        execution = self.runbook_service.execute_runbook(runbook_id, requested_by, approved_by)
        return execution.__dict__

    def _suggest_runbook(self, lowered: str) -> AssistantSuggestion | None:
        runbook = self.runbook_service.suggest_runbook(lowered)
        if runbook is None:
            return None
        action = AssistantAction(
            action_id=str(uuid.uuid4()),
            action_type="runbook.execute",
            title=f"Execute runbook: {runbook.name}",
            summary=runbook.description,
            requires_approval=runbook.requires_approval,
            payload={"runbook_id": runbook.runbook_id},
        )
        return AssistantSuggestion(intent="runbook", confidence=0.75, actions=[action])

    def _suggest_install(self, lowered: str) -> AssistantSuggestion | None:
        if "install" not in lowered:
            return None
        templates = self.install_service.list_templates()
        for template in templates:
            if template.component in lowered:
                action = AssistantAction(
                    action_id=str(uuid.uuid4()),
                    action_type="install.plan",
                    title=f"Prepare install: {template.component}",
                    summary=f"Template {template.component} ({template.kind})",
                    requires_approval=True,
                    payload={"component": template.component},
                )
                return AssistantSuggestion(intent="install", confidence=0.65, actions=[action])
        return None
