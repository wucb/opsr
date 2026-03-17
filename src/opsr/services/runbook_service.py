from __future__ import annotations

import uuid
from datetime import datetime, timezone

from opsr.models.runbook import ApprovalRequest, Runbook, RunbookExecution
from opsr.repositories.runbook_repository import (
    InMemoryApprovalRepository,
    InMemoryRunbookExecutionRepository,
    InMemoryRunbookRepository,
)


class RunbookService:
    """Milestone 2.4: runbook execution + approval workflow."""

    def __init__(
        self,
        runbook_repository: InMemoryRunbookRepository | None = None,
        approval_repository: InMemoryApprovalRepository | None = None,
        execution_repository: InMemoryRunbookExecutionRepository | None = None,
    ) -> None:
        self.runbook_repository = runbook_repository or InMemoryRunbookRepository()
        self.approval_repository = approval_repository or InMemoryApprovalRepository()
        self.execution_repository = execution_repository or InMemoryRunbookExecutionRepository()

    def list_runbooks(self) -> list[Runbook]:
        return self.runbook_repository.list_runbooks()

    def suggest_runbook(self, request_text: str) -> Runbook | None:
        text = request_text.lower()
        if "redis" in text:
            return self.runbook_repository.get("rb-redis-restart")
        if "mysql" in text or "backup" in text:
            return self.runbook_repository.get("rb-mysql-backup")
        return None

    def request_approval(self, runbook_id: str, requested_by: str) -> ApprovalRequest:
        approval = ApprovalRequest(
            approval_id=str(uuid.uuid4()),
            runbook_id=runbook_id,
            requested_by=requested_by,
            status="pending",
        )
        self.approval_repository.add(approval)
        return approval

    def decide_approval(self, approval_id: str, approved: bool, decided_by: str) -> ApprovalRequest | None:
        approval = self.approval_repository.get(approval_id)
        if approval is None:
            return None
        approval.status = "approved" if approved else "rejected"
        approval.decided_at = datetime.now(timezone.utc)
        approval.decided_by = decided_by
        return approval

    def execute_runbook(self, runbook_id: str, requested_by: str, approved_by: str | None) -> RunbookExecution:
        execution = RunbookExecution(
            execution_id=str(uuid.uuid4()),
            runbook_id=runbook_id,
            status="running",
            requested_by=requested_by,
            approved_by=approved_by,
        )
        runbook = self.runbook_repository.get(runbook_id)
        if runbook is None:
            execution.status = "failed"
            execution.logs.append("runbook not found")
            execution.finished_at = datetime.now(timezone.utc)
            self.execution_repository.add(execution)
            return execution

        for step in runbook.steps:
            execution.logs.append(f"execute {step.step_id}: {step.command}")
        execution.status = "success"
        execution.finished_at = datetime.now(timezone.utc)
        self.execution_repository.add(execution)
        return execution

    def list_approvals(self) -> list[ApprovalRequest]:
        return self.approval_repository.list_approvals()

    def list_executions(self) -> list[RunbookExecution]:
        return self.execution_repository.list_executions()
