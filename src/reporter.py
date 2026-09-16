from __future__ import annotations

import json
from pathlib import Path

from .action_manager import create_action_record
from .models import EventCard


def print_terminal_report(cards: list[EventCard], total_alarm_count: int) -> None:
    reduced_alarm_count = sum(c.alarm_count for c in cards)
    print("=" * 96)
    print("ALERT STORM CORRELATOR - OLAY KARTLARI")
    print("=" * 96)
    print(
        f"Toplam alarm: {total_alarm_count} | Kart sayısı: {len(cards)} | "
        f"Korelasyona dahil alarm: {reduced_alarm_count}"
    )
    print("-" * 96)

    for card in cards:
        print(f"[{card.event_id}] {card.root_cause_hypothesis}")
        print(f"  - Root Service: {card.root_service}")
        print(f"  - Etkilenen Servisler: {', '.join(card.impacted_services[:12])}")
        print(f"  - Alarm Sayısı: {card.alarm_count}")
        print(f"  - Zaman Aralığı: {card.start_time.isoformat()} -> {card.end_time.isoformat()}")
        print(f"  - Güven Skoru: {card.confidence}")
        print(f"  - İlk Aksiyon: {card.first_action_suggestion}")
        print(f"  - Sahip/Durum: {card.owner} / {card.status}")
        print(f"  - Why Root Cause: {card.why_root_cause}")
        print(f"  - Why Noise: {card.why_noise}")
        print("-" * 96)


def export_json(cards: list[EventCard], output_path: Path) -> None:
    payload = []
    for card in cards:
        action = create_action_record(card)
        payload.append(
            {
                "event_id": card.event_id,
                "root_cause_hypothesis": card.root_cause_hypothesis,
                "root_service": card.root_service,
                "impacted_services": card.impacted_services,
                "alarm_count": card.alarm_count,
                "start_time": card.start_time.isoformat(),
                "end_time": card.end_time.isoformat(),
                "confidence": card.confidence,
                "why_root_cause": card.why_root_cause,
                "why_noise": card.why_noise,
                "action": {
                    "action_id": action.action_id,
                    "owner": action.owner,
                    "status": action.status,
                    "first_action": action.first_action,
                },
                "alarm_ids": card.alarm_ids,
                "noise_alarm_ids": card.noise_alarm_ids,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_html(cards: list[EventCard], output_path: Path) -> None:
    rows = []
    for c in cards:
        rows.append(
            f"""
            <tr>
              <td>{c.event_id}</td>
              <td>{c.root_service}</td>
              <td>{c.alarm_count}</td>
              <td>{c.start_time.isoformat()} - {c.end_time.isoformat()}</td>
              <td>{c.owner}</td>
              <td>{c.status}</td>
              <td>{c.first_action_suggestion}</td>
              <td>{c.why_root_cause}</td>
              <td>{c.why_noise}</td>
            </tr>
            """
        )

    html = f"""
    <!doctype html>
    <html lang=\"tr\">
    <head>
      <meta charset=\"utf-8\" />
      <title>Alert Storm Correlator</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #0f172a; color: #e2e8f0; }}
        h1 {{ color: #38bdf8; }}
        table {{ width: 100%; border-collapse: collapse; background: #111827; }}
        th, td {{ border: 1px solid #374151; padding: 8px; vertical-align: top; }}
        th {{ background: #1f2937; }}
      </style>
    </head>
    <body>
      <h1>Alert Storm Correlator - Olay Kartları</h1>
      <table>
        <thead>
          <tr>
            <th>Event</th><th>Root</th><th>Alarm</th><th>Zaman</th><th>Sahip</th><th>Durum</th><th>İlk Aksiyon</th><th>Neden Root</th><th>Neden Gürültü</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </body>
    </html>
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
