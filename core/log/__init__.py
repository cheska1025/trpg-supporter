from __future__ import annotations

from datetime import datetime
from pathlib import Path


def append_markdown(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(f"- {datetime.now().isoformat(timespec='seconds')} {text}\n")
