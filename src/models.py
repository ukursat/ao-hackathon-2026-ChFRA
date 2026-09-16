from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Alarm:
    alarm_id: str
    timestamp: datetime
    source_system: str
    host: str
    service: str
    severity: int
    alarm_type: str
    message: str
    tags: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionRecord:
    action_id: str
    owner: str
    status: str
    first_action: str


@dataclass(slots=True)
class EventCard:
    event_id: str
    root_cause_hypothesis: str
    root_service: str
    impacted_services: list[str]
    alarm_count: int
    start_time: datetime
    end_time: datetime
    confidence: float | None
    first_action_suggestion: str
    owner: str
    status: str
    why_root_cause: str
    why_noise: str
    alarm_ids: list[str] = field(default_factory=list)
    noise_alarm_ids: list[str] = field(default_factory=list)
