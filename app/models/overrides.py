"""
ColumnOverride model — represents a user-specified reinterpretation of a
single column's inferred type.

Allowed override_type values:
    LIKERT    — treat column as a Likert scale (1–5)
    BOOLEAN   — treat column as boolean (0/1)
    NUMERIC   — treat column as a numeric measurement
    TEXT      — treat column as free text / nominal
    IGNORE    — exclude column from analysis
"""
from dataclasses import dataclass

ALLOWED_OVERRIDE_TYPES: frozenset = frozenset(
    {"LIKERT", "BOOLEAN", "NUMERIC", "TEXT", "IGNORE"}
)


@dataclass
class ColumnOverride:
    dataset_id: str
    column_name: str
    override_type: str

    def __post_init__(self) -> None:
        if self.override_type not in ALLOWED_OVERRIDE_TYPES:
            raise ValueError(
                f"Invalid override_type: {self.override_type!r}. "
                f"Allowed: {sorted(ALLOWED_OVERRIDE_TYPES)}"
            )
