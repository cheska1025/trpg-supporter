from __future__ import annotations

from datetime import datetime
from pathlib import Path


def append_markdown(path: str | Path, text: str) -> None:
    """단순 md 로그 누적: 'YYYY-MM-DD HH:MM' + 텍스트 한 줄"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"- {ts} {text}\n")
