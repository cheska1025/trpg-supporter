from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


# 단일 라인 추가(기존 함수 유지):
def append_markdown(path: str | Path, text: str) -> None:
    """한 줄 로그를 'YYYY-MM-DD HH:MM' 타임스탬프와 함께 누적"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"- {ts} {text}\n")


@dataclass
class LogEntry:
    channel: str  # "system" | "narrative"
    text: str
    timestamp: datetime


class SessionLog:
    def __init__(self) -> None:
        self.entries: list[LogEntry] = []

    def add(self, channel: str, text: str) -> None:
        self.entries.append(LogEntry(channel=channel, text=text, timestamp=datetime.now()))

    def extend(self, rows: Iterable[LogEntry]) -> None:
        self.entries.extend(rows)

    def export_md(self, path: str | Path) -> None:
        """채널별 섹션을 가진 Markdown 파일로 내보내기"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        system = [e for e in self.entries if e.channel == "system"]
        narrative = [e for e in self.entries if e.channel == "narrative"]

        def _lines(items: list[LogEntry]) -> list[str]:
            return [f"- {e.timestamp.strftime('%Y-%m-%d %H:%M')} {e.text}" for e in items]

        with p.open("w", encoding="utf-8") as f:
            f.write("# Session Log\n\n")
            f.write("## System\n")
            f.write("\n".join(_lines(system)) + ("\n\n" if system else "\n"))
            f.write("## Narrative\n")
            f.write("\n".join(_lines(narrative)) + ("\n" if narrative else "\n"))

    def export_json(self, path: str | Path) -> None:
        """원시 레코드(JSON Array)로 내보내기"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "channel": e.channel,
                "text": e.text,
                "timestamp": e.timestamp.isoformat(timespec="minutes"),
            }
            for e in self.entries
        ]
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
