from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from backend.app.core.db import session_scope
from backend.app.models import LogEntry

# 내보내기 루트
EXPORTS = Path("exports")
EXPORTS.mkdir(parents=True, exist_ok=True)

Channel = Literal["system", "narrative"]


@dataclass(slots=True)
class LogItem:
    channel: Channel
    text: str
    # 초 단위까지 고정 문자열 (예: "2025-08-16 10:14:35")
    timestamp: str


def _paths(session_id: int) -> tuple[Path, Path]:
    """세션별 MD/JSON 경로."""
    md = EXPORTS / f"session_{session_id}.md"
    js = EXPORTS / f"session_{session_id}.json"
    return md, js


def _now_str() -> str:
    """현재 시각을 초 단위까지 문자열로 반환."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_json(path: Path) -> list[dict]:
    """UTF-8/BOM 여부와 상관없이 JSON을 로드. 없거나 파싱 실패 시 []"""
    if not path.exists():
        return []
    try:
        # BOM 유무에 무관한 디코딩을 위해 utf-8-sig
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return []


def _save_json(path: Path, data: list[dict]) -> None:
    """Windows PowerShell `type`에서도 한글이 깨지지 않도록 UTF-8 with BOM으로 저장."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8-sig")


_MD_SKELETON = "# Session Log\n\n## System\n\n## Narrative\n"


def _save_md(path: Path, items: Iterable[LogItem]) -> None:
    """
    채널별 섹션으로 렌더링해 저장. PowerShell 출력 호환을 위해 UTF-8 with BOM.
    - System 섹션은 머리말 직후에 누적
    - Narrative 섹션은 파일 말미에 누적
    """
    sys_lines: list[str] = []
    narr_lines: list[str] = []
    for it in items:
        line = f"- {it.timestamp} {it.text}"
        if it.channel == "system":
            sys_lines.append(line)
        else:
            narr_lines.append(line)

    lines: list[str] = [
        "# Session Log",
        "",
        "## System",
        "",
        *sys_lines,
        "",
        "## Narrative",
        "",
        *narr_lines,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8-sig")


def _same_second_key(item: LogItem) -> tuple[str, str, str]:
    """중복 판정을 위한 키: (channel, text, timestamp[:19])"""
    return (item.channel, item.text, item.timestamp[:19])


def _dedup_exists(items: Iterable[LogItem], new_item: LogItem) -> bool:
    """
    '같은 초 단위'에 동일 channel+text가 하나라도 존재하면 True(=이미 있음).
    마지막 항목만 보던 기존 방식에서 전체 검색으로 강화.
    """
    key = _same_second_key(new_item)
    for it in items:
        if _same_second_key(it) == key:
            return True
    return False


def append_session_log(*, session_id: int, channel: Channel, text: str) -> dict[str, str]:
    """
    DB에 LogEntry 저장 + 로컬 export 파일 갱신(.json → .md).
    - JSON을 싱글 소스로 보고, MD는 JSON을 기반으로 재생성
    - '같은 초 단위의 동일 channel+text'가 이미 있으면 중복 추가하지 않음
    """
    # 1) DB 저장
    with session_scope() as s:
        s.add(
            LogEntry(
                session_id=session_id,
                category="system" if channel == "system" else "narrative",
                message=text,
            )
        )

    # 2) 파일 갱신(JSON 우선 → MD 재생성)
    md_path, json_path = _paths(session_id)
    items_raw = _load_json(json_path)
    items: list[LogItem] = [
        LogItem(
            channel=(it.get("channel") or "system"),  # 안전 기본값
            text=(it.get("text") or ""),
            timestamp=(it.get("timestamp") or ""),
        )
        for it in items_raw
    ]

    new_item = LogItem(channel=channel, text=text, timestamp=_now_str())
    if not _dedup_exists(items, new_item):
        items.append(new_item)
    # else: 같은 초 단위 동일 라인이 존재 → 추가 생략

    # JSON 저장(UTF-8 with BOM)
    _save_json(json_path, [asdict(x) for x in items])
    # MD 저장(UTF-8 with BOM)
    _save_md(md_path, items)

    return {"md": str(md_path), "json": str(json_path)}


def export_session_log(*, session_id: int) -> dict[str, str]:
    """
    JSON을 싱글 소스로 보고 MD를 재구성(덮어쓰기).
    파일이 없다면 기본 스켈레톤으로 생성.
    """
    md_path, json_path = _paths(session_id)

    items_raw = _load_json(json_path)
    items: list[LogItem] = [
        LogItem(
            channel=(it.get("channel") or "system"),
            text=(it.get("text") or ""),
            timestamp=(it.get("timestamp") or ""),
        )
        for it in items_raw
    ]

    # 파일이 비어 있어도 스켈레톤 형태의 MD를 만들어 준다
    _save_md(md_path, items)
    # JSON 파일이 없었다면 빈 배열로 생성
    if not json_path.exists():
        _save_json(json_path, [])

    return {"md": str(md_path), "json": str(json_path)}


# (선택) CLI의 slog list 구현 시 활용 가능: 채널/개수 제한 조회
def list_session_log(
    *,
    session_id: int,
    channel: Channel | None = None,
    limit: int | None = None,
) -> list[dict]:
    """
    JSON 기반 조회 유틸.
    - channel: "system" / "narrative" 로 필터
    - limit: 앞에서부터 최대 N개
    """
    _, json_path = _paths(session_id)
    items_raw = _load_json(json_path)
    # 정제
    rows: list[dict] = []
    for it in items_raw:
        ch = it.get("channel") or "system"
        if channel and ch != channel:
            continue
        rows.append(
            {
                "timestamp": (it.get("timestamp") or ""),
                "channel": ch,
                "text": (it.get("text") or ""),
            }
        )
    if limit and limit > 0:
        rows = rows[:limit]
    return rows
