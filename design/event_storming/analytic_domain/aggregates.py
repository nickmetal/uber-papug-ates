from dataclasses import dataclass
from decimal import Decimal
from typing import Dict


@dataclass
class DailyStats:
    """Cколько заработал топ-менеджмент за сегодня и сколько попугов ушло в минус."""
    daily_amount: Decimal
    currency: str
    papug_with_negative_score_count: int
    

@dataclass
class TopTasksInfo:
    """Нужно показывать самую дорогую задачу за день, неделю или месяц."""
    task_per_day: {date: str, task_fee: str, currency: str}
    task_per_week: {week: str, task_fee: str, currency: str}
    task_month_week: {month: str, task_fee: str, currency: str}

