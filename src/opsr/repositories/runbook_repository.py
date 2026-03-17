from __future__ import annotations

from opsr.models.runbook import ApprovalRequest, Runbook, RunbookExecution


class InMemoryRunbookRepository:
    def __init__(self) -> None:
        self._runbooks: dict[str, Runbook] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        from opsr.models.runbook import RunbookStep

        self.add(
            Runbook(
                runbook_id="rb-redis-restart",
                name="Redis Restart",
                description="Restart Redis service and validate health.",
                steps=[
                    RunbookStep(step_id="1", description="Restart service", command="systemctl restart redis"),
                    RunbookStep(step_id="2", description="Health check", command="redis-cli ping"),
                ],
            )
        )
        self.add(
            Runbook(
                runbook_id="rb-mysql-backup",
                name="MySQL Backup",
                description="Trigger logical backup to /data/backup.",
                steps=[
                    RunbookStep(step_id="1", description="Prepare backup dir", command="mkdir -p /data/backup"),
                    RunbookStep(step_id="2", description="Dump database", command="mysqldump --all-databases > /data/backup/all.sql"),
                ],
            )
        )

    def add(self, runbook: Runbook) -> None:
        self._runbooks[runbook.runbook_id] = runbook

    def list_runbooks(self) -> list[Runbook]:
        return list(self._runbooks.values())

    def get(self, runbook_id: str) -> Runbook | None:
        return self._runbooks.get(runbook_id)


class InMemoryApprovalRepository:
    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRequest] = {}

    def add(self, approval: ApprovalRequest) -> None:
        self._approvals[approval.approval_id] = approval

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._approvals.get(approval_id)

    def list_approvals(self) -> list[ApprovalRequest]:
        return list(self._approvals.values())


class InMemoryRunbookExecutionRepository:
    def __init__(self) -> None:
        self._executions: dict[str, RunbookExecution] = {}

    def add(self, execution: RunbookExecution) -> None:
        self._executions[execution.execution_id] = execution

    def list_executions(self) -> list[RunbookExecution]:
        return list(self._executions.values())
