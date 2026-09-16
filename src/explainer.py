"""Kanıt açıklaması ortak analiz motorunda üretilir, LLM taklidi yapılmaz."""
from pathlib import Path

from .models import Alarm, EventCard


def generate_explanations(cards: list[EventCard], all_alarms: list[Alarm],
                          prompts_dir: Path) -> list[EventCard]:
    """Uyumluluk adaptörü: prompt metnini model çıktısı gibi eklemez."""
    return cards