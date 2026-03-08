from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Dataset:
    dataset_id: str
    file_path: str
    row_count: int
    column_count: int
    columns: List[str]
    created_at: datetime = field(default_factory=_now_utc)
