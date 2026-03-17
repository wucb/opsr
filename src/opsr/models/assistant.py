from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class AssistantAction:
    action_id: str
    action_type: str
    title: str
    summary: str
    requires_approval: bool = True
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class AssistantSuggestion:
    intent: str
    confidence: float
    actions: list[AssistantAction] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AssistantRequest:
    text: str
    requested_by: str
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class AssistantResponse:
    request: AssistantRequest
    suggestions: list[AssistantSuggestion]
