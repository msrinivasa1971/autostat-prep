"""
Dataset lifecycle state machine.

Valid transitions:
    UPLOADED → NORMALIZING
    NORMALIZING → COMPLETE
    NORMALIZING → FAILED

Any other transition raises ValueError.
"""
from enum import Enum
from typing import Dict, FrozenSet


class DatasetState(str, Enum):
    UPLOADED = "UPLOADED"
    NORMALIZING = "NORMALIZING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


_VALID_TRANSITIONS: Dict[DatasetState, FrozenSet[DatasetState]] = {
    DatasetState.UPLOADED: frozenset({DatasetState.NORMALIZING}),
    DatasetState.NORMALIZING: frozenset({DatasetState.COMPLETE, DatasetState.FAILED}),
    DatasetState.COMPLETE: frozenset(),
    DatasetState.FAILED: frozenset(),
}


def validate_transition(current: DatasetState, target: DatasetState) -> None:
    """Raise ValueError if the transition current → target is not permitted."""
    allowed = _VALID_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        allowed_names = [s.value for s in sorted(allowed, key=lambda s: s.value)] or ["none"]
        raise ValueError(
            f"Invalid state transition: {current.value} → {target.value}. "
            f"Allowed from {current.value}: {allowed_names}"
        )
