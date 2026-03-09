from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from app.models.state import DatasetState, validate_transition


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
    dataset_hash: str = ""
    state: DatasetState = field(default_factory=lambda: DatasetState.UPLOADED)

    def transition(self, new_state: DatasetState) -> None:
        """
        Advance the dataset to new_state.

        Raises ValueError if the transition is not permitted by the state machine.
        """
        validate_transition(self.state, new_state)
        self.state = new_state
