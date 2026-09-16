from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path

import networkx as nx

from .models import Alarm


def load_alarms(alarms_path: Path) -> list[Alarm]:
    raw = json.loads(alarms_path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, list):
        raise ValueError("alarms.json bir JSON dizisi olmalıdır.")
    alarms: list[Alarm] = []
    seen: set[str] = set()
    for row in raw:
        required = ("alarm_id", "timestamp", "host", "service", "severity", "alarm_type")
        if any(key not in row for key in required):
            raise ValueError("Eksik zorunlu alarm alanı.")
        if type(row["severity"]) is not int or row["severity"] not in range(1, 6):
            raise ValueError("Severity 1–5 arasında tam sayı olmalıdır.")
        if not row["alarm_id"] or row["alarm_id"] in seen:
            raise ValueError("Boş veya tekrarlanan alarm_id.")
        seen.add(row["alarm_id"])
        alarms.append(
            Alarm(
                alarm_id=row["alarm_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                source_system=row.get("source_system", "unknown"),
                host=row["host"],
                service=row["service"],
                severity=int(row["severity"]),
                alarm_type=row["alarm_type"],
                message=row.get("message", ""),
                tags=row.get("tags", {}),
            )
        )
    if len({a.timestamp.tzinfo is None for a in alarms}) > 1:
        raise ValueError("Saat dilimli ve saat dilimsiz kayıtlar karıştırılamaz.")
    alarms.sort(key=lambda x: (x.timestamp, x.alarm_id))
    return alarms


def load_service_graph(dependencies_path: Path) -> nx.DiGraph:
    graph = nx.DiGraph()
    with dependencies_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = row["kaynak_servis"].strip()
            dst = row["hedef_servis"].strip()
            graph.add_edge(
                src,
                dst,
                bagimlilik_tipi=row.get("bagimlilik_tipi", "bilinmiyor"),
                kritiklik=row.get("kritiklik", "orta"),
            )
    return graph


def load_host_inventory(host_inventory_path: Path) -> dict[str, dict[str, str]]:
    inventory: dict[str, dict[str, str]] = {}
    with host_inventory_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["host"].strip() in inventory:
                raise ValueError("Envanterde tekrarlanan host.")
            inventory[row["host"].strip()] = {
                "service": row["servis"].strip(),
                "dc": row["veri_merkezi"].strip(),
                "rack": row["kabin"].strip(),
                "env": row["ortam"].strip(),
                "business_criticality": row["is_kritikligi"].strip(),
            }
    return inventory


def load_dataset(data_dir: Path) -> tuple[list[Alarm], nx.DiGraph, dict[str, dict[str, str]]]:
    """Önce sözlük, sonra tüm kayıtlar. Saat dilimsiz verilere UTC eklenmez."""
    dictionary = (data_dir / "VERI_SOZLUGU.md").read_text(encoding="utf-8-sig")
    known_types = set(re.findall(r"^\| `([a-z_0-9]+)` \|", dictionary, re.MULTILINE))
    if not known_types:
        raise ValueError("Veri sözlüğünden alarm tipleri okunamadı.")
    alarms = load_alarms(data_dir / "alarms.json")
    graph = load_service_graph(data_dir / "service_dependencies.csv")
    inventory = load_host_inventory(data_dir / "host_inventory.csv")
    for alarm in alarms:
        if alarm.alarm_type not in known_types:
            raise ValueError(f"Sözlükte olmayan alarm tipi: {alarm.alarm_type}")
        host = inventory.get(alarm.host)
        if host is None or host["service"] != alarm.service:
            raise ValueError(f"Host/servis envanter uyuşmazlığı: {alarm.alarm_id}")
    graph.add_nodes_from(row["service"] for row in inventory.values())
    return alarms, graph, inventory
