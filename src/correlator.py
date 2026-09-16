"""Eski EventCard arayüzü için ortak analiz motoru adaptörü."""
from datetime import datetime

import networkx as nx

from .analysis import correlate
from .models import Alarm, EventCard


def cards_from_result(result: dict) -> list[EventCard]:
    return [EventCard(
        event_id=c["event_id"], root_cause_hypothesis=c["root_cause_hypothesis"],
        root_service=c["root_service"], impacted_services=c["impacted_services"],
        alarm_count=c["alarm_count_total"],
        start_time=datetime.fromisoformat(c["time_window"]["start"]),
        end_time=datetime.fromisoformat(c["time_window"]["end"]),
        confidence=None, first_action_suggestion=c["action"]["first_action"],
        owner=c["action"]["owner"], status=c["action"]["status"],
        why_root_cause=c["why_root_cause"],
        why_noise="Bağımsız zayıf sinyaller ayrı audit dosyasında; türev etkiler kartta korunur.",
        alarm_ids=c["alarm_ids"], noise_alarm_ids=[],
    ) for c in result["event_cards"]]


def correlate_alarms(alarms: list[Alarm], graph: nx.DiGraph,
                     max_cards: int = 15) -> list[EventCard]:
    result = correlate(alarms, graph, max_cards=max_cards)
    if result["deferred_incidents"]:
        raise ValueError("Kart limiti aşıldı; kayıpsız sonuç için analysis.correlate kullanın.")
    return cards_from_result(result)