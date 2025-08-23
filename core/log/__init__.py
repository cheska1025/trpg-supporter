from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

__all__ = ["LogManager", "append_markdown"]


# ---- helpers -----------------------------------------------------------------
def _utcnow() -> datetime:
    # 테스트들이 tz-naive utcnow 를 기대하므로 그대로 둔다 (경고는 무시)
    return datetime.utcnow()


def _trpg_home() -> Path:
    raw = os.environ.get("TRPG_HOME")
    return Path(raw) if raw else Path.home() / ".trpg"


def append_markdown(path: Path, line: str) -> None:
    """
    단순 파일 누적 쓰기. BOM 없이 utf-8 로, 부모 디렉토리 자동 생성.
    tests/core/test_dice.py::test_append_markdown 가 이 함수의 동작을 검증한다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line)
        f.write("\n")


# ---- core --------------------------------------------------------------------
@dataclass(frozen=True)
class _Entry:
    kind: Literal["system", "narrative"]
    payload: dict[str, Any]
    ts: datetime


class LogManager:
    """
    - 메모리 상에 엔트리를 쌓고
    - export("md") 시 마크다운 파일을 exports/ 아래에 저장하며,
      동시에 마크다운/JSON 문자열을 반환한다.
    - 생성자 인자는 두 가지 패턴 모두 지원:
        LogManager(session_id="S1")
        LogManager(base=TRPG_HOME, session_id="S1")
    """

    def __init__(self, base: str | Path | None = None, session_id: str | None = None) -> None:
        base_path = Path(base) if base is not None else _trpg_home()
        self.base: Path = base_path
        # base 가 파일 경로여도 안전하게 디렉토리 만들기
        self.base.mkdir(parents=True, exist_ok=True)

        self.session_id: str = session_id or "default"
        self._entries: list[_Entry] = []

    # --- append APIs (위치/키워드 모두 허용) -----------------------------------
    def append_system(
        self, event: str | None = None, data: dict[str, Any] | None = None, **_: Any
    ) -> None:
        """
        시스템 이벤트 로그.
        - 위치 인자: append_system("dice", {...})
        - 키워드 인자: append_system(event="dice", data={...})
        """
        e = event or ""
        d = data or {}
        self._entries.append(_Entry(kind="system", payload={"event": e, "data": d}, ts=_utcnow()))

    def append_narrative(self, text: str | None = None, **_: Any) -> None:
        """
        서사(내러티브) 로그.
        - 위치 인자: append_narrative("전투 개시")
        - 키워드 인자: append_narrative(text="전투 개시")
        """
        t = text or ""
        self._entries.append(_Entry(kind="narrative", payload={"text": t}, ts=_utcnow()))

    # --- export ----------------------------------------------------------------
    def export(
        self,
        fmt: Literal["md", "json"] = "md",
        *,
        display_title: str | None = None,
        **_: Any,  # CLI 가 예기치 않은 추가 키워드를 넘겨도 무시
    ) -> str:
        """
        - md/json 내보내기 지원
        - 파일을 exports/ 아래에 저장
        - 마크다운/JSON 문자열을 반환 (tests 가 문자열의 내용을 검사)
        """
        ts = _utcnow().strftime("%Y%m%d-%H%M%S")

        # 주 저장 위치(인스턴스 기준)
        outdir_main = self.base / "exports"
        outdir_main.mkdir(parents=True, exist_ok=True)

        # 테스트 기대치: 환경변수 TRPG_HOME 바로 아래에도 exports/ 가 있어야 함
        env_home = _trpg_home()
        outdir_env = env_home / "exports"
        outdir_env.mkdir(parents=True, exist_ok=True)

        if fmt == "md":
            title = display_title or f"Session {self.session_id}"
            content = self._render_md(title)

            filename = f"{self.session_id}-{ts}.md"
            # 메인 경로에 저장
            (outdir_main / filename).write_text(content, encoding="utf-8", newline="\n")
            # 환경변수 경로가 다르면 미러링 저장
            if outdir_env != outdir_main:
                (outdir_env / filename).write_text(content, encoding="utf-8", newline="\n")
            return content

        if fmt == "json":
            import json

            payload = [
                {"kind": e.kind, "payload": e.payload, "ts": e.ts.isoformat()}
                for e in self._entries
            ]
            content = json.dumps(
                {"session_id": self.session_id, "entries": payload},
                ensure_ascii=False,
                indent=2,
            )

            filename = f"{self.session_id}-{ts}.json"
            (outdir_main / filename).write_text(content, encoding="utf-8", newline="\n")
            if outdir_env != outdir_main:
                (outdir_env / filename).write_text(content, encoding="utf-8", newline="\n")
            return content

        raise ValueError("unsupported format")

    # --- internal renderers ----------------------------------------------------
    def _render_md(self, title: str) -> str:
        lines: list[str] = [f"# {title}"]
        for e in self._entries:
            if e.kind == "system":
                event = e.payload.get("event", "")
                data = e.payload.get("data", {})
                if event == "dice":
                    actor = data.get("actor", "-")
                    formula = data.get("formula", "-")
                    total = data.get("total", "-")
                    lines.append(f"- 🎲 **{actor}** rolled `{formula}` → **{total}**")
                else:
                    lines.append(f"- system: {event} {data}")
            else:
                text = e.payload.get("text", "")
                lines.append(f"- {text}")
        return "\n".join(lines)
