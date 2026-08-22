from datetime import datetime, timezone
from typing import Any


def parse_datetime_param(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        val_str = val.strip()
        if not val_str:
            return None
        # Handle cases where HTTP decodes '+' to ' ' in URL query strings (e.g., ...T12:00:00 00:00)
        if " " in val_str:
            parts = val_str.rsplit(" ", 1)
            if len(parts) == 2 and (":" in parts[1] or len(parts[1]) == 4):
                val_str = f"{parts[0]}+{parts[1]}"
            else:
                val_str = val_str.replace(" ", "T")
        try:
            dt = datetime.fromisoformat(val_str)
            return dt
        except ValueError:
            pass
    return None
