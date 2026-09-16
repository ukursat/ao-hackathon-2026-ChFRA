from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analysis import correlate
from .correlator import cards_from_result
from .data_loader import load_dataset
from .reporter import export_html, export_json, print_terminal_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alert Storm Correlator")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Veri klasörü")
    parser.add_argument("--prompts-dir", type=Path, default=Path("prompts"), help="Prompt klasörü")
    parser.add_argument("--max-cards", type=int, choices=range(1, 16), default=15,
                        help="Kart üst sınırı (1–15); hedef mümkün olan en az anlamlı olay")
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("demo/event_cards.json"),
        help="JSON çıktı yolu",
    )
    parser.add_argument(
        "--out-html",
        type=Path,
        default=Path("demo/event_cards.html"),
        help="HTML çıktı yolu",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()

    alarms, graph, inventory = load_dataset(args.data_dir)
    result = correlate(alarms, graph, inventory, max_cards=args.max_cards)
    cards = cards_from_result(result)

    print_terminal_report(cards, total_alarm_count=len(alarms))
    export_json(cards, args.out_json)
    export_html(cards, args.out_html)

    analysis_path = args.out_json.with_name("analysis_result.json")
    analysis_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["correlation_summary"], ensure_ascii=False))
    for warning in result["warnings"]:
        print(f"UYARI: {warning}")

    print(f"\nJSON çıktı: {args.out_json}")
    print(f"HTML çıktı: {args.out_html}")


if __name__ == "__main__":
    main()
