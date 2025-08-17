# core/log/__init__.py
from __future__ import annotations

import json
import os
from collections.abc import Iterable  # Optional 제거
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

__all__ = ["LogManager", "append_markdown"]

# 산출물/저널 기본 위치
_EXPORT_DIRNAME = "exports"  # <TRPG_HOME>/exports
_LOG_DIRNAME = "logs"  # <TRPG_HOME>/logs
_TS_FMT_FILE = "%Y%m%d-%H%M%S"  # 파일명 타임스탬프 포맷


# --------- 경로/시간 유틸 ---------
def _home_root() -> Path:
    base = os.getenv("TRPG_HOME")
    if base:
        return Path(base)
    return Path.home() / ".trpg"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _fmt_ts_for_md(ts: str) -> str:
    return ts.replace("T", " ")


# --------- 데이터 모델 ---------
@dataclass
class _LogItem:
    """
    로그 1건.
      - type: "system" | "narrative"
      - system용: event, data
      - narrative용: text, scene
    """

    type: Literal["system", "narrative"]
    ts: str
    event: str | None = None  # 예: "dice", "encounter", "init", ...
    data: dict | None = None  # 시스템 이벤트 세부 데이터
    text: str | None = None  # 내러티브 텍스트
    scene: str | None = None  # 내러티브 씬 이름


# --------- LogManager ---------
class LogManager:
    """
    세션 로그 관리자 (저널 지속 기록 방식)

    - 생성자 인자: session_id (고유 ID, 파일 키로 사용)
    - append_system(event, data) / append_narrative(text, scene=None)
      => 즉시 <TRPG_HOME>/logs/<session_id>.jsonl 에 1줄씩 append

    - export(fmt, display_title=None)
      => 저널을 읽어 <TRPG_HOME>/exports/<session_id>-<ts>.(md|json) 생성
         * display_title가 있으면 Markdown 헤더에 사용 (사람용 제목)
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        root = _home_root()
        self._log_dir = root / _LOG_DIRNAME
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._journal_path = self._log_dir / f"{session_id}.jsonl"

    # ---------- append (지속 기록) ----------
    def append_system(self, event: str, data: dict[str, Any]) -> None:
        item = _LogItem(type="system", ts=_now_iso(), event=event, data=data or {})
        self._append_journal(item)

    def append_narrative(self, text: str, scene: str | None = None) -> None:
        item = _LogItem(type="narrative", ts=_now_iso(), text=text, scene=scene)
        self._append_journal(item)

    def _append_journal(self, item: _LogItem) -> None:
        self._journal_path.parent.mkdir(parents=True, exist_ok=True)
        with self._journal_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

    # ---------- 읽기 ----------
    def _iter_items(self) -> Iterable[_LogItem]:
        if not self._journal_path.exists():
            return iter(())

        def gen():
            with self._journal_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    yield _LogItem(**d)

        return gen()

    # ---------- export ----------
    def export(self, fmt: Literal["md", "json"], display_title: str | None = None) -> str:
        root = _home_root()
        export_dir = root / _EXPORT_DIRNAME
        export_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime(_TS_FMT_FILE)
        items = list(self._iter_items())

        # JSON 내보내기
        if fmt == "json":
            path = export_dir / f"{self.session_id}-{ts}.json"
            with path.open("w", encoding="utf-8") as f:
                json.dump([asdict(i) for i in items], f, ensure_ascii=False, indent=2)
            return str(path)

        # Markdown 내보내기
        if fmt == "md":
            path = export_dir / f"{self.session_id}-{ts}.md"
            title_for_header = display_title or self.session_id
            with path.open("w", encoding="utf-8") as f:
                # 문서 헤더
                f.write(f"# Session {title_for_header}\n\n")

                # 섹션 분류
                rolls = [i for i in items if i.type == "system" and i.event == "dice"]
                narratives = [i for i in items if i.type == "narrative"]
                others = [i for i in items if i.type == "system" and i.event != "dice"]

                # Rolls 섹션
                if rolls:
                    f.write("## Rolls\n")
                    for it in rolls:
                        data = it.data or {}
                        actor = data.get("actor")
                        formula = data.get("formula", "?")
                        total = data.get("total", "?")
                        detail = data.get("detail")
                        ts_md = _fmt_ts_for_md(it.ts)

                        if detail is None:
                            detail_s = "[]"
                        else:
                            detail_s = json.dumps(detail, ensure_ascii=False)

                        head = f"- [{ts_md}] "
                        if actor:
                            head += f"**{actor}**: "
                        f.write(head + f"`{formula}` → **{total}** (detail: {detail_s})\n")
                    f.write("\n")

                # Narrative 섹션
                if narratives:
                    f.write("## Narrative\n")
                    for it in narratives:
                        ts_md = _fmt_ts_for_md(it.ts)
                        scene = f" *({it.scene})*" if it.scene else ""
                        text = it.text or ""
                        f.write(f"- [{ts_md}]{scene} {text}\n")
                    f.write("\n")

                # System 섹션(기타)
                if others:
                    f.write("## System\n")
                    for it in others:
                        ts_md = _fmt_ts_for_md(it.ts)
                        event = it.event or "system"
                        data_s = json.dumps(it.data or {}, ensure_ascii=False)
                        f.write(f"- [{ts_md}] **{event}**: {data_s}\n")
                    f.write("\n")

            return str(path)

        raise ValueError(f"unsupported format: {fmt}")


# ---------- 호환용 유틸 ----------
def append_markdown(path: str | os.PathLike, line: str) -> str:
    """
    지정된 파일 경로에 마크다운 한 줄을 append.
    - 부모 디렉터리가 없으면 생성
    - 반환: 최종 파일 경로(str)
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")
    return str(p)
