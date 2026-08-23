import json
from pathlib import Path
from typing import Any

import pandas as pd


def load_json_file(file_path: str | Path) -> list[dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def load_csv_file(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV dataset file not found: {path}")
    return pd.read_csv(path)
