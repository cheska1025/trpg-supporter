# core/log/__init__.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Literal

__all__ = ["LogManager", "append_markdown"]

_EXPORT_DIRNAME = "exports"


def _home_root() -> Path:
    """TRPG_HOME이 설정되어 있으면 그 경로를, 아니면 ~/.trpg 를 반환."""
    base = os.getenv("TRPG_HOME")
    if base:
        return Path(base)
    return Path.home() / ".trpg"


@dataclass
class _LogItem:
    type: Literal["system", "narrative"]
    ts: str
    event: Optional[str] = None
    data: Optional[dict] = None
    text: Optional[str] = None
    scene: Optional[str] = None


class LogManager:
    """
    세션 로그 관리(최소 구현):
      - append_system(event, data)
      - append_narrative(text, scene=None)
      - export(fmt="md"|"json") -> 생성된 파일 경로(str) 반환
    출력 디렉토리: <TRPG_HOME>/exports (없으면 생성)
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._items: List[_LogItem] = []

    # ---------- append ----------
    def append_system(self, event: str, data: dict[str, Any]) -> None:
        self._items.append(
            _LogItem(type="system", ts=self._now(), event=event, data=data)
        )

    def append_narrative(self, text: str, scene: Optional[str] = None) -> None:
        self._items.append(
            _LogItem(type="narrative", ts=self._now(), text=text, scene=scene)
        )

    # ---------- export ----------
    def export(self, fmt: Literal["md", "json"]) -> str:
        """
        fmt="json"  -> <TRPG_HOME>/exports/<session>-<ts>.json
        fmt="md"    -> <TRPG_HOME>/exports/<session>-<ts>.md
        반환: 생성된 파일의 절대경로 문자열
        """
        root = _home_root()
        export_dir = root / _EXPORT_DIRNAME
        export_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d-%H%M%S")

        if fmt == "json":
            path = export_dir / f"{self.session_id}-{ts}.json"
            with path.open("w", encoding="utf-8") as f:
                json.dump([asdict(i) for i in self._items], f, ensure_ascii=False, indent=2)
            return str(path)

        if fmt == "md":
            path = export_dir / f"{self.session_id}-{ts}.md"
            with path.open("w", encoding="utf-8") as f:
                f.write(f"# Session {self.session_id}\n\n")
                for it in self._items:
                    if it.type == "system":
                        data_s = json.dumps(it.data, ensure_ascii=False)
                        f.write(f"- **[{it.ts}] SYSTEM/{it.event}**: {data_s}\n")
                    else:
                        scene = f" ({it.scene})" if it.scene else ""
                        f.write(f"- **[{it.ts}] NARRATIVE{scene}**: {it.text}\n")
            return str(path)

        raise ValueError(f"unsupported format: {fmt}")

    # ---------- utils ----------
    @staticmethod
    def _now() -> str:
        # 초 단위까지 통일된 ISO 포맷
        return datetime.now().isoformat(timespec="seconds")


def append_markdown(path: str | os.PathLike, line: str) -> str:
    """
    호환용 헬퍼: 지정한 파일 경로에 마크다운 한 줄을 append.
    - 부모 디렉터리가 없으면 생성
    - 반환: 최종 파일 경로(str)
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")
    return str(p)
