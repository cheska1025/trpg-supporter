# core/log/__init__.py
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

# Windows PowerShell에서도 한글이 안 깨지도록 BOM 포함 UTF-8 사용
ENCODING = "utf-8-sig"

Channel = Literal["system", "narrative"]


@dataclass(slots=True)
class LogEntry:
    """
    세션 로그 1건.
    - channel: "system" | "narrative"
    - text: 로그 본문
    - timestamp: 기록 시각 (초 단위까지 사용)
    """

    channel: Channel
    text: str
    timestamp: datetime


class SessionLog:
    """
    메모리 상에서 로그를 축적하고, .md / .json으로 내보내는 저장소.
    특징:
    - add() 시 '최근 몇 초 내 동일 channel+text'는 중복 기록 방지
    - export 시 시간순 정렬 보장
    - .md는 채널 섹션별로 출력 (# Session Log / ## System / ## Narrative)
    """

    def __init__(self, *, dedup_seconds: int = 2) -> None:
        # dedup_seconds: 같은 channel+text가 N초 이내면 중복으로 간주하여 무시
        self.entries: list[LogEntry] = []
        self._dedup_window = timedelta(seconds=max(0, dedup_seconds))

    # ---------------------------
    # 기록/조회
    # ---------------------------
    def add(self, channel: Channel, text: str, *, at: datetime | None = None) -> bool:
        """
        로그 추가. 중복으로 간주되면 False(미추가), 추가되면 True 반환.
        """
        ts = (at or datetime.now()).replace(microsecond=0)

        if self._is_duplicate(channel, text, ts):
            return False

        self.entries.append(LogEntry(channel=channel, text=text, timestamp=ts))
        return True

    def list(self) -> list[LogEntry]:
        """시간순 정렬된 로그 목록 반환(복사)."""
        return sorted(self.entries, key=lambda e: e.timestamp)

    def extend(self, items: Iterable[LogEntry]) -> None:
        """외부에서 가져온 로그를 일괄 추가(중복 필터링 적용)."""
        for it in items:
            self.add(it.channel, it.text, at=it.timestamp)

    # ---------------------------
    # 내보내기 (파일)
    # ---------------------------
    def export_json(self, path: str | Path) -> None:
        """
        JSON 형식으로 저장.
        [
          {"channel": "system", "text": "...", "timestamp": "YYYY-MM-DD HH:MM:SS"},
          ...
        ]
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        data = [
            {
                "channel": e.channel,
                "text": e.text,
                "timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for e in self.list()
        ]
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=ENCODING)

    def export_md(self, path: str | Path) -> None:
        """
        Markdown 형식으로 저장. 채널별 섹션에 시간순으로 나열.
        # Session Log

        ## System
        - 2025-08-16 10:01:00 라운드 시작

        ## Narrative
        - 2025-08-16 10:01:10 적이 모습을 드러낸다
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        system_lines: list[str] = []
        narrative_lines: list[str] = []

        for e in self.list():
            line = f"- {e.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {e.text}"
            if e.channel == "system":
                system_lines.append(line)
            else:
                narrative_lines.append(line)

        lines: list[str] = ["# Session Log", ""]
        # System 섹션
        lines.append("## System")
        if system_lines:
            lines.extend(system_lines)
        lines.append("")  # 섹션 간 빈 줄

        # Narrative 섹션
        lines.append("## Narrative")
        if narrative_lines:
            lines.extend(narrative_lines)
        lines.append("")

        p.write_text("\n".join(lines), encoding=ENCODING)

    # ---------------------------
    # 내부 유틸
    # ---------------------------
    def _is_duplicate(self, channel: Channel, text: str, ts: datetime) -> bool:
        """
        최근 self._dedup_window 내의 항목 중
        channel+text가 동일하면 중복으로 간주.
        """
        if not self.entries or self._dedup_window.total_seconds() <= 0:
            return False

        # 최근 항목들만 확인 (역순 탐색)
        threshold = ts - self._dedup_window
        for e in reversed(self.entries):
            if e.timestamp < threshold:
                break
            if e.channel == channel and e.text == text:
                return True
        return False


# ------------------------------------------------------------
# [Deprecated] 구 CLI 호환: 한 줄씩 .md에 직접 추가하는 함수
#  - 새로운 CLI에서는 SessionLog를 사용하는 것을 권장.
# ------------------------------------------------------------
def append_markdown(path: str | Path, text: str) -> None:
    """
    내러티브 섹션에 한 줄을 추가한다.
    (가능한 SessionLog 사용 권장. 이 함수는 기존 CLI 호환용.)
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # 파일이 없으면 스켈레톤 생성
    if not p.exists():
        skeleton = "# Session Log\n\n## System\n\n## Narrative\n"
        p.write_text(skeleton, encoding=ENCODING)

    ts = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    line = f"- {ts} {text}"

    content = p.read_text(encoding=ENCODING)
    # 이미 동일 라인이 존재하면 추가하지 않음
    if line in content:
        return

    # "## Narrative" 섹션 바로 아래에 안전하게 삽입
    anchor = "## Narrative"
    if anchor in content:
        head, tail = content.split(anchor, 1)
        if not tail.startswith("\n"):
            tail = "\n" + tail
        new_tail = tail.rstrip() + "\n" + line + "\n"
        p.write_text(head + anchor + new_tail, encoding=ENCODING)
    else:
        # 섹션이 없다면 파일을 재구성
        skeleton = "# Session Log\n\n## System\n\n## Narrative\n"
        p.write_text(skeleton + line + "\n", encoding=ENCODING)
