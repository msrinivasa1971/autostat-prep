from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    user_id: str
    email: str
    created_at: datetime = field(default_factory=_now_utc)
