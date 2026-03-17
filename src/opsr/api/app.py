from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from opsr.models.install import InstallRequest
from opsr.models.monitoring import AlertRule, MetricSample
from opsr.services.assistant_service import AssistantService
from opsr.services.compliance_service import ComplianceService
from opsr.services.install_service import InstallOrchestrationService
from opsr.services.monitoring_service import MonitoringService
from opsr.services.runbook_service import RunbookService

app = FastAPI(title="OpsR API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_service = InstallOrchestrationService()
monitoring_service = MonitoringService()
runbook_service = RunbookService()
compliance_service = ComplianceService()
assistant_service = AssistantService(runbook_service=runbook_service, install_service=install_service)


class InstallRequestSchema(BaseModel):
    component: str
    target_host: str
    config: dict[str, Any] = Field(default_factory=dict)
    requested_by: str = "api"


class MetricSampleSchema(BaseModel):
    name: str
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


class AlertRuleSchema(BaseModel):
    rule_id: str
    metric_name: str
    comparator: str
    threshold: float
    severity: str
    description: str = ""
    labels: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True


class SuggestRunbookSchema(BaseModel):
    text: str


class ApprovalRequestSchema(BaseModel):
    runbook_id: str
    requested_by: str = "api"


class ApprovalDecisionSchema(BaseModel):
    approval_id: str
    approved: bool
    decided_by: str = "api"


class RunbookExecuteSchema(BaseModel):
    runbook_id: str
    requested_by: str = "api"
    approved_by: str | None = None


class ComplianceCheckSchema(BaseModel):
    observations: dict[str, Any] = Field(default_factory=dict)


class DriftCheckSchema(BaseModel):
    resource_id: str
    desired: dict[str, Any] = Field(default_factory=dict)
    current: dict[str, Any] = Field(default_factory=dict)


class AssistantTriageSchema(BaseModel):
    text: str
    requested_by: str = "api"


class AssistantExecuteSchema(BaseModel):
    runbook_id: str
    requested_by: str = "api"
    approved_by: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/install/templates")
def list_templates(kind: str | None = None) -> list[dict[str, Any]]:
    templates = install_service.list_templates(kind)
    return [template.__dict__ for template in templates]


@app.post("/install/submit")
def submit_install(request: InstallRequestSchema) -> dict[str, Any]:
    result = install_service.submit_install(
        InstallRequest(
            component=request.component,
            target_host=request.target_host,
            config=request.config,
            requested_by=request.requested_by,
        )
    )
    if result.status == "failed" and result.errors and result.errors[0].startswith("unknown component"):
        raise HTTPException(status_code=400, detail=result.errors)
    return {
        "status": result.status,
        "request": {
            "component": result.request.component,
            "target_host": result.request.target_host,
            "config": result.request.config,
            "requested_by": result.request.requested_by,
        },
        "steps": [step.__dict__ for step in result.steps],
        "errors": result.errors,
    }


@app.get("/install/results")
def list_results() -> list[dict[str, Any]]:
    results = install_service.list_results()
    payload: list[dict[str, Any]] = []
    for result in results:
        payload.append(
            {
                "status": result.status,
                "request": {
                    "component": result.request.component,
                    "target_host": result.request.target_host,
                    "config": result.request.config,
                    "requested_by": result.request.requested_by,
                },
                "steps": [step.__dict__ for step in result.steps],
                "errors": result.errors,
            }
        )
    return payload


@app.post("/monitoring/rules")
def create_rule(rule: AlertRuleSchema) -> dict[str, Any]:
    monitoring_service.add_rule(
        AlertRule(
            rule_id=rule.rule_id,
            metric_name=rule.metric_name,
            comparator=rule.comparator,
            threshold=rule.threshold,
            severity=rule.severity,
            description=rule.description,
            labels=rule.labels,
            enabled=rule.enabled,
        )
    )
    return {"status": "ok"}


@app.get("/monitoring/rules")
def list_rules() -> list[dict[str, Any]]:
    return [rule.__dict__ for rule in monitoring_service.list_rules()]


@app.post("/monitoring/ingest")
def ingest_metric(sample: MetricSampleSchema) -> dict[str, Any]:
    events = monitoring_service.ingest_sample(
        MetricSample(name=sample.name, value=sample.value, labels=sample.labels)
    )
    return {"events": [event.__dict__ for event in events]}


@app.get("/monitoring/events")
def list_events(limit: int = 200) -> list[dict[str, Any]]:
    return [event.__dict__ for event in monitoring_service.list_events(limit)]


@app.get("/runbooks")
def list_runbooks() -> list[dict[str, Any]]:
    return [runbook.__dict__ for runbook in runbook_service.list_runbooks()]


@app.post("/runbooks/suggest")
def suggest_runbook(payload: SuggestRunbookSchema) -> dict[str, Any]:
    runbook = runbook_service.suggest_runbook(payload.text)
    if runbook is None:
        return {"match": None}
    return {"match": runbook.__dict__}


@app.post("/runbooks/approvals")
def request_approval(payload: ApprovalRequestSchema) -> dict[str, Any]:
    approval = runbook_service.request_approval(payload.runbook_id, payload.requested_by)
    return approval.__dict__


@app.post("/runbooks/approvals/decide")
def decide_approval(payload: ApprovalDecisionSchema) -> dict[str, Any]:
    approval = runbook_service.decide_approval(payload.approval_id, payload.approved, payload.decided_by)
    if approval is None:
        raise HTTPException(status_code=404, detail="approval not found")
    return approval.__dict__


@app.get("/runbooks/approvals")
def list_approvals() -> list[dict[str, Any]]:
    return [approval.__dict__ for approval in runbook_service.list_approvals()]


@app.post("/runbooks/execute")
def execute_runbook(payload: RunbookExecuteSchema) -> dict[str, Any]:
    execution = runbook_service.execute_runbook(payload.runbook_id, payload.requested_by, payload.approved_by)
    return execution.__dict__


@app.get("/runbooks/executions")
def list_executions() -> list[dict[str, Any]]:
    return [execution.__dict__ for execution in runbook_service.list_executions()]


@app.get("/compliance/baselines")
def list_baselines() -> list[dict[str, Any]]:
    return [baseline.__dict__ for baseline in compliance_service.list_baselines()]


@app.post("/compliance/check")
def run_baseline_checks(payload: ComplianceCheckSchema) -> list[dict[str, Any]]:
    results = compliance_service.run_checks(payload.observations)
    return [result.__dict__ for result in results]


@app.post("/compliance/drift")
def detect_drift(payload: DriftCheckSchema) -> dict[str, Any]:
    drift = compliance_service.detect_drift(payload.resource_id, payload.desired, payload.current)
    return drift.__dict__


@app.get("/compliance/results")
def list_compliance_results() -> list[dict[str, Any]]:
    return [result.__dict__ for result in compliance_service.list_results()]


@app.get("/compliance/drifts")
def list_drift_results() -> list[dict[str, Any]]:
    return [drift.__dict__ for drift in compliance_service.list_drifts()]


@app.get("/compliance/report")
def compliance_report(period: str = "daily") -> dict[str, object]:
    return compliance_service.report(period)


@app.post("/assistant/triage")
def assistant_triage(payload: AssistantTriageSchema) -> dict[str, Any]:
    response = assistant_service.triage(payload.text, payload.requested_by)
    return {
        "request": response.request.__dict__,
        "suggestions": [suggestion.__dict__ for suggestion in response.suggestions],
    }


@app.post("/assistant/runbooks/approve")
def assistant_approve(payload: ApprovalRequestSchema) -> dict[str, Any]:
    approval = assistant_service.request_runbook_approval(payload.runbook_id, payload.requested_by)
    return approval


@app.post("/assistant/runbooks/execute")
def assistant_execute(payload: AssistantExecuteSchema) -> dict[str, Any]:
    execution = assistant_service.execute_runbook(payload.runbook_id, payload.requested_by, payload.approved_by)
    return execution