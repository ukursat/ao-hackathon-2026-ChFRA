"""MCP ve CLI için ortak, deterministik ve tamamen bellek içi analiz."""
from __future__ import annotations

from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import timedelta
from typing import Any

import networkx as nx

from .action_manager import guess_owner
from .models import Alarm

WINDOW = timedelta(minutes=10)
MERGE_GAP = timedelta(minutes=30)
MAINTENANCE = {"cert_expiry", "log_rotate", "ntp_drift", "backup_warn"}


def _near(times: list, timestamp) -> bool:
    index = bisect_left(times, timestamp)
    return any(abs(times[i] - timestamp) <= WINDOW
               for i in (index - 1, index) if 0 <= i < len(times))


def filter_noise(alarms: list[Alarm], graph: nx.DiGraph) -> tuple[list[Alarm], list[dict]]:
    """Zayıf sinyal yalnızca yakın güçlü/topolojik kanıt yoksa bastırılır."""
    strong: dict[str, list] = defaultdict(list)
    for alarm in alarms:
        if alarm.severity >= 3 and alarm.alarm_type not in MAINTENANCE:
            strong[alarm.service].append(alarm.timestamp)
    for times in strong.values():
        times.sort()
    neighborhoods = {
        service: {service} | nx.ancestors(graph, service) | nx.descendants(graph, service)
        for service in graph
    }
    signal, audit = [], []
    for alarm in alarms:
        weak = alarm.severity <= 2 or (
            alarm.severity <= 3 and alarm.alarm_type in MAINTENANCE
        )
        supported = any(_near(strong[s], alarm.timestamp)
                        for s in neighborhoods[alarm.service])
        if weak and not supported:
            audit.append({
                "alarm_id": alarm.alarm_id, "service": alarm.service,
                "host": alarm.host, "timestamp": alarm.timestamp.isoformat(),
                "classification": "suppressed_noise",
                "reason_code": "WEAK_WITHOUT_NEARBY_TOPOLOGY_SIGNAL",
                "evidence": {
                    "severity": alarm.severity,
                    "alarm_type": alarm.alarm_type,
                    "message": alarm.message,
                    "maintenance_type": alarm.alarm_type in MAINTENANCE,
                    "window_start": (alarm.timestamp - WINDOW).isoformat(),
                    "window_end": (alarm.timestamp + WINDOW).isoformat(),
                    "checked_services": sorted(neighborhoods[alarm.service]),
                    "strong_signal_definition": "severity >= 3 ve bakım tipi değil",
                    "nearby_strong_signal_count": 0,
                    "nearby_strong_signal_alarm_ids": [],
                },
                "reason": "Düşük şiddetli/bakım sinyali; ±10 dakikada aynı servis veya "
                          "bağımlılık zincirinde güçlü arıza sinyali yok. "
                          "Bastırma hipotezidir, gerçek gürültü etiketi değildir.",
            })
        else:
            signal.append(alarm)
    return signal, audit


def correlate(alarms: list[Alarm], graph: nx.DiGraph,
              inventory: dict | None = None, max_cards: int = 15) -> dict[str, Any]:
    # 15 hedef değil üst sınırdır; bağımsız olaylar sayı uğruna birleştirilmez.
    if type(max_cards) is not int or not 1 <= max_cards <= 15:
        raise ValueError("max_cards 1–15 arasında tam sayı olmalıdır.")
    alarms = sorted(alarms, key=lambda a: (a.timestamp, a.alarm_id))
    if len({a.alarm_id for a in alarms}) != len(alarms):
        raise ValueError("Tekrarlanan alarm_id.")
    graph = graph.copy()
    graph.add_nodes_from(a.service for a in alarms)
    inventory = inventory or {}
    signal, audit = filter_noise(alarms, graph)

    # Servis bazlı oturum: ardışık sinyaller <=10 dk ise saat sınırı aşılabilir.
    episodes: dict[int, list[Alarm]] = {}
    by_service: dict[str, list[int]] = defaultdict(list)
    for alarm in signal:
        nodes = by_service[alarm.service]
        if not nodes or alarm.timestamp - episodes[nodes[-1]][-1].timestamp > WINDOW:
            node = len(episodes)
            episodes[node] = []
            nodes.append(node)
        episodes[nodes[-1]].append(alarm)

    active = nx.DiGraph()
    active.add_nodes_from(episodes)
    # A→B yalnızca yakın gerçek alarm zamanlarıyla desteklenirse etkinleştirilir.
    for source, target in graph.edges:
        for a in by_service[source]:
            for b in by_service[target]:
                times = [row.timestamp for row in episodes[b]]
                if any(_near(times, row.timestamp) for row in episodes[a]):
                    active.add_edge(a, b)

    # SCC döngüleri tek belirsiz kök bileşen olarak tutar; sonsuz dolaşım yoktur.
    dag = nx.condensation(active)
    def root_priority(component: int) -> tuple:
        rows = [a for n in dag.nodes[component]["members"] for a in episodes[n]]
        return (-max(a.severity for a in rows), min(a.timestamp for a in rows),
                min(a.service for a in rows), component)

    grouped: dict[int, dict] = {}
    for node in sorted(active):
        component = dag.graph["mapping"][node]
        reachable = nx.descendants(dag, component) | {component}
        candidates = sorted((c for c in reachable if dag.out_degree(c) == 0),
                            key=root_priority)
        root = candidates[0]
        root_nodes = sorted(dag.nodes[root]["members"])
        root_services = sorted({episodes[n][0].service for n in root_nodes})
        group = grouped.setdefault(root, {
            "root_services": root_services, "rows": [], "assignments": [],
            "candidate_roots": set(), "paths": {},
        })
        group["candidate_roots"].update(
            episodes[n][0].service for c in candidates for n in dag.nodes[c]["members"]
        )
        target = next(n for n in root_nodes if nx.has_path(active, node, n))
        path = [episodes[n][0].service for n in nx.shortest_path(active, node, target)]
        group["paths"][episodes[node][0].service] = path
        role = "root_signal" if component == root else "derived_effect"
        for alarm in episodes[node]:
            group["rows"].append(alarm)
            group["assignments"].append({
                "alarm_id": alarm.alarm_id, "classification": role,
                "graph_path": path,
                "reason": "Aktif bağımlılık zincirinin uç kök bileşeni." if role == "root_signal"
                else "A→B aktif bağımlılık yolunda türev etki adayı; silinmedi, olayda korundu.",
            })

    # Aynı kökteki yakın oturumları birleştir: yavaş gelişen olay korunur.
    merged: list[dict] = []
    for group in sorted(grouped.values(), key=lambda g: (
        g["root_services"], min(a.timestamp for a in g["rows"])
    )):
        group["rows"].sort(key=lambda a: (a.timestamp, a.alarm_id))
        if (merged and merged[-1]["root_services"] == group["root_services"]
                and group["rows"][0].timestamp - merged[-1]["rows"][-1].timestamp <= MERGE_GAP):
            previous = merged[-1]
            previous["rows"].extend(group["rows"])
            previous["rows"].sort(key=lambda a: (a.timestamp, a.alarm_id))
            previous["assignments"].extend(group["assignments"])
            previous["candidate_roots"].update(group["candidate_roots"])
            previous["paths"].update(group["paths"])
        else:
            merged.append(group)

    merged.sort(key=lambda g: (-max(a.severity for a in g["rows"]),
                              -len(g["rows"]), g["rows"][0].timestamp, g["root_services"]))
    cards, metrics = [], {}
    for index, group in enumerate(merged, 1):
        rows = group["rows"]
        root_ids = {x["alarm_id"] for x in group["assignments"]
                    if x["classification"] == "root_signal"}
        root_rows = [a for a in rows if a.alarm_id in root_ids]
        evidence = min(root_rows, key=lambda a: (-a.severity, a.timestamp, a.alarm_id))
        event_id = f"EVT-{index:03d}"
        duration = (rows[-1].timestamp - rows[0].timestamp).total_seconds()
        explanation = (
            f"Kök aday {evidence.service}: {evidence.alarm_id} ({evidence.alarm_type}). "
            "Kaynak→hedef aktif bağımlılık zincirinde hedef yönündeki uç bileşen seçildi. "
            "Birden çok adayda şiddet, erken başlangıç ve servis adı ile deterministik sıralama yapıldı. "
            "Zaman yakınlığı nedenselliği kanıtlamaz; ortak ağ arızası elenmiş değildir."
        )
        card = {
            "event_id": event_id, "root_service": evidence.service,
            "root_component_services": group["root_services"],
            "root_cause_hypothesis": f"{evidence.service}: {evidence.alarm_type} arıza hipotezi.",
            "impacted_services": sorted({a.service for a in rows}),
            "time_window": {"start": rows[0].timestamp.isoformat(), "end": rows[-1].timestamp.isoformat()},
            "duration_seconds": duration, "long_running": duration >= 1800,
            "alarm_count_total": len(rows), "alarm_count_root_signal": len(root_ids),
            "alarm_count_derived_effect": len(rows) - len(root_ids),
            "alarm_ids": [a.alarm_id for a in rows], "root_signal_alarm_ids": sorted(root_ids),
            "derived_alarm_ids": [a.alarm_id for a in rows if a.alarm_id not in root_ids],
            "severity": max(a.severity for a in rows),
            "action": {"owner": guess_owner(evidence.service), "status": "Açık",
                       "first_action": f"{evidence.host} üzerinde {evidence.alarm_type} sinyalini "
                       "metrik/log ile doğrula; son değişiklikleri ve bağımlılık sağlığını kontrol et."},
            "why_root_cause": explanation,
        }
        cards.append(card)
        serialized = []
        for alarm in rows:
            item = asdict(alarm)
            item["timestamp"] = alarm.timestamp.isoformat()
            item["inventory"] = inventory.get(alarm.host, {})
            serialized.append(item)
        metrics[event_id] = {
            "event_card": card, "candidate_root_services": sorted(group["candidate_roots"]),
            "cycle_ambiguity": len(group["root_services"]) > 1,
            "severity_counts": dict(sorted(Counter(a.severity for a in rows).items())),
            "alarm_type_counts": dict(sorted(Counter(a.alarm_type for a in rows).items())),
            "service_metrics": [{"service": service, "alarm_count": len(service_rows),
                "first_seen": min(a.timestamp for a in service_rows).isoformat(),
                "last_seen": max(a.timestamp for a in service_rows).isoformat(),
                "hosts": sorted({a.host for a in service_rows})}
                for service in card["impacted_services"]
                for service_rows in [[a for a in rows if a.service == service]]],
            "alarm_assignments": group["assignments"], "alarms": serialized,
            "counter_hypothesis": "Ortak altyapı arızası veya bağımsız eşzamanlı olaylar "
            "elenemedi; trace, ağ metriği ve değişiklik kayıtları gerekir.",
            "limitations": ["Doğrulanmış RCA değil, topolojik hipotezdir.",
                            "İlk/son alarm aralığı gerçek SLA kesinti süresi değildir.",
                            "Şiddet sıralaması kalibre edilmiş olasılık değildir."],
        }

    selected = cards[:max_cards]
    deferred = cards[max_cards:]
    # Sınır aşımı gürültü değildir: tüm olay ve alarm ID'leri ayrıca korunur.
    all_ids = [aid for card in cards for aid in card["alarm_ids"]] + [x["alarm_id"] for x in audit]
    if len(all_ids) != len(set(all_ids)) or set(all_ids) != {a.alarm_id for a in alarms}:
        raise RuntimeError("Alarm muhasebesi tutarsız: kayıp veya çift sınıflandırma.")
    return {
        "dataset": {"total_alarms": len(alarms), "sampling_used": False,
                    "hosts": len({a.host for a in alarms}), "services": len(graph)},
        "correlation_summary": {"event_card_count": len(selected),
            "candidate_event_count": len(cards), "max_event_card_limit": max_cards,
            "suppressed_noise_count": len(audit),
            "derived_effect_count": sum(c["alarm_count_derived_effect"] for c in cards),
            "alarms_in_selected_cards": sum(c["alarm_count_total"] for c in selected),
            "deferred_alarm_count": sum(c["alarm_count_total"] for c in deferred),
            "accounted_alarm_count": len(all_ids)},
        "event_cards": selected, "deferred_incidents": deferred,
        "warnings": ["Kart limiti aşıldı; ertelenen olaylar gürültü sayılmadı."] if deferred else [],
        "noise_audit_log": audit, "rca_metrics": metrics,
    }