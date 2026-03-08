from dataclasses import dataclass


@dataclass
class ColumnSchema:
    column_name: str
    column_type: str       # Always "TEXT" in Sprint-1
    missing_ratio: float   # 0.0 – 1.0
    unique_values: int
