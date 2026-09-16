from __future__ import annotations

from .models import ActionRecord, EventCard


OWNER_RULES: list[tuple[str, str]] = [
    ("db", "DBA-OnCall"),
    ("gateway", "Platform-OnCall"),
    ("bff", "Platform-OnCall"),
    ("api", "Platform-OnCall"),
    ("payment", "CoreBiz-OnCall"),
    ("billing", "CoreBiz-OnCall"),
    ("order", "CoreBiz-OnCall"),
    ("subscriber", "CoreBiz-OnCall"),
]


def guess_owner(service_name: str) -> str:
    service = service_name.lower()
    for pattern, owner in OWNER_RULES:
        if pattern in service:
            return owner
    return "SRE-OnCall"


def create_action_record(event: EventCard) -> ActionRecord:
    return ActionRecord(
        action_id=f"ACT-{event.event_id}",
        owner=event.owner,
        status=event.status,
        first_action=event.first_action_suggestion,
    )
