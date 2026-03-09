"""
Override service — persist and retrieve column overrides for a dataset.

Storage location: storage/users/{user_id}/datasets/{dataset_id}/overrides.json
"""
import json
from pathlib import Path
from typing import List

from app.config import get_dataset_dir
from app.models.overrides import ColumnOverride


def load_overrides(dataset_id: str, user_id: str = "default") -> List[ColumnOverride]:
    """
    Load saved column overrides for a dataset.
    Returns an empty list if no overrides file exists.
    """
    path = get_dataset_dir(user_id, dataset_id) / "overrides.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ColumnOverride(
            dataset_id=dataset_id,
            column_name=entry["column_name"],
            override_type=entry["override_type"],
        )
        for entry in data.get("overrides", [])
    ]


def save_overrides(
    dataset_id: str,
    overrides: List[ColumnOverride],
    user_id: str = "default",
) -> Path:
    """
    Persist column overrides to the dataset directory.

    Returns the path to the written file.
    """
    d = get_dataset_dir(user_id, dataset_id)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "overrides.json"
    payload = {
        "dataset_id": dataset_id,
        "overrides": [
            {"column_name": o.column_name, "override_type": o.override_type}
            for o in overrides
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
