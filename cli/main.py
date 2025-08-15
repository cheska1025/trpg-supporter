from __future__ import annotations

import json
from pathlib import Path

import click
from rich import print as rprint

from core.dice import roll
from core.initiative import Tracker
from core.log import SessionLog, append_markdown  # append_markdown은 하위 호환용(선택)

# --- 이니시 상태 영구 저장 위치 ---
STATE = Path.home() / ".trpg" / "init_state.json"
STATE.parent.mkdir(parents=True, exist_ok=True)

# --- 세션 로그(메모리) ---
_log = SessionLog()


def _save_tracker(tr: Tracker) -> None:
    data = {
        "round": tr.round,
        "idx": tr.idx,
        "entries": [{"name": e.name, "value": e.value, "delayed": e.delayed} for e in tr.entries],
    }
    STATE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _load_tracker() -> Tracker:
    tr = Tracker()
    if STATE.exists():
        data = json.loads(STATE.read_text(encoding="utf-8"))
        tr.round = int(data.get("round", 1))
        tr.idx = int(data.get("idx", 0))
        for it in data.get("entries", []):
            tr.add(str(it["name"]), int(it["value"]))
        # 안전 범위로 idx 보정
        tr.idx = min(tr.idx, max(len(tr.entries) - 1, 0))
    return tr


@click.group(
    help=(
        "TRPG Supporter CLI (MVP)\n\n"
        "주요 명령 예시:\n"
        '  trpg roll "2d6+3"\n'
        "  trpg init add Rogue 17\n"
        "  trpg init update Rogue 14\n"
        "  trpg init remove Rogue\n"
        "  trpg init delay Rogue / trpg init resume Rogue\n"
        "  trpg init prev / trpg init next / trpg init tick\n"
        '  trpg log add --channel system --msg "세션 시작"\n'
        "  trpg log export --format md --out ./exports/session.md\n"
    )
)
def cli() -> None:
    """TRPG Supporter CLI"""


# ---- 주사위 ----
@cli.command("roll", help='주사위 굴림 (예: trpg roll "2d6+3")')
@click.argument("formula")
def rollcmd(formula: str) -> None:
    res = roll(formula)
    rprint({"formula": res.formula, "rolls": res.rolls, "total": res.total})


# ---- 이니시 ----
@cli.group(
    help="이니시 명령군: add / update / remove / delay / resume / prev / next / tick / reset"
)
def init() -> None:
    """이니시 그룹"""


@init.command("add", help="이니시 등록 (예: trpg init add Rogue 17)")
@click.argument("name")
@click.argument("value", type=int)
def init_add(name: str, value: int) -> None:
    tr = _load_tracker()
    tr.add(name, value)
    _save_tracker(tr)
    rprint([{"name": e.name, "value": e.value, "delayed": e.delayed} for e in tr.entries])


@init.command("update", help="이니시 수치 수정 (예: trpg init update Rogue 14)")
@click.argument("name")
@click.argument("value", type=int)
def init_update(name: str, value: int) -> None:
    tr = _load_tracker()
    found = False
    for e in tr.entries:
        if e.name == name:
            e.value = value
            found = True
    if not found:
        rprint({"error": f"'{name}' 항목을 찾지 못했습니다."})
        return
    # 값 변경 후 재정렬 및 인덱스 보정
    tr.entries.sort()
    tr.idx = min(tr.idx, max(len(tr.entries) - 1, 0))
    _save_tracker(tr)
    rprint([{"name": e.name, "value": e.value, "delayed": e.delayed} for e in tr.entries])


@init.command("remove", help="이니시 삭제 (예: trpg init remove Rogue)")
@click.argument("name")
def init_remove(name: str) -> None:
    tr = _load_tracker()
    before = len(tr.entries)
    tr.entries = [e for e in tr.entries if e.name != name]
    after = len(tr.entries)
    if before == after:
        rprint({"error": f"'{name}' 항목을 찾지 못했습니다."})
        return
    # 삭제 후 인덱스 보정
    if tr.idx >= len(tr.entries):
        tr.idx = 0 if tr.entries else 0
    _save_tracker(tr)
    rprint([{"name": e.name, "value": e.value, "delayed": e.delayed} for e in tr.entries])


@init.command("delay", help="보류 처리(턴 스킵) (예: trpg init delay Rogue)")
@click.argument("name")
def init_delay(name: str) -> None:
    tr = _load_tracker()
    try:
        tr.delay(name)
    except Exception as e:  # 구현에 맞춰 예외형 바꿔도 됨
        rprint({"error": str(e)})
        return
    _save_tracker(tr)
    rprint({"delayed": name})


@init.command("resume", help="보류 해제 후 재진입 (예: trpg init resume Rogue)")
@click.argument("name")
def init_resume(name: str) -> None:
    tr = _load_tracker()
    try:
        tr.resume(name)
    except Exception as e:
        rprint({"error": str(e)})
        return
    cur = tr.current()
    _save_tracker(tr)
    rprint({"resumed": name, "current": None if cur is None else cur.name})


@init.command("prev", help="이전 턴으로 이동")
def init_prev() -> None:
    tr = _load_tracker()
    cur = tr.prev()
    _save_tracker(tr)
    rprint({"round": tr.round, "current": None if cur is None else cur.name})


@init.command("next", help="다음 턴으로 진행(라운드 자동 증가)")
def init_next() -> None:
    tr = _load_tracker()
    cur = tr.next()
    _save_tracker(tr)
    rprint({"round": tr.round, "current": None if cur is None else cur.name})


@init.command("tick", help="상태효과 남은 라운드 일괄 감소")
def init_tick() -> None:
    tr = _load_tracker()
    tr.tick_effects()
    _save_tracker(tr)
    rprint({"effects": "ticked"})


@init.command("reset", help="이니시 상태 초기화")
def init_reset() -> None:
    if STATE.exists():
        STATE.unlink()
    rprint({"reset": True})


# ---- 로그 ----
@cli.group(help="세션 로그 명령군: add / export")
def log() -> None:
    """세션 로그 그룹"""


@log.command("add", help='로그 적재 (예: trpg log add --channel system --msg "세션 시작")')
@click.option(
    "--channel", type=click.Choice(["system", "narrative"]), required=True, help="로그 채널"
)
@click.option("--msg", required=True, help="로그 텍스트")
def log_add(channel: str, msg: str) -> None:
    _log.add(channel=channel, text=msg)
    rprint({"added": {"channel": channel, "text": msg}})


@log.command("export", help="메모리 로그를 파일로 내보내기 (md|json)")
@click.option(
    "--format", "fmt", type=click.Choice(["md", "json"]), required=True, help="내보내기 형식"
)
@click.option("--out", default="./exports/session.md", show_default=True)
def log_export(fmt: str, out: str) -> None:
    if fmt == "md":
        _log.export_md(out)
    else:
        if out.endswith(".md"):
            out = out.replace(".md", ".json")
        _log.export_json(out)
    rprint({"saved": out})


# (선택) 하위 호환: 바로 Markdown에 1줄 추가
@cli.command("logmd", help='단일 줄을 Markdown에 즉시 추가 (예: trpg logmd --msg "세션 시작")')
@click.option("--msg", required=True, help="로그 텍스트")
@click.option("--out", default="./exports/session.md", show_default=True)
def logmd(msg: str, out: str) -> None:
    append_markdown(out, msg)
    rprint({"saved": out})


# ---- 버전 ----
@cli.command(help="패키지 버전 표시(개발 중이면 dev)")
def version() -> None:
    from importlib.metadata import PackageNotFoundError, version

    try:
        rprint({"trpg-supporter": version("trpg-supporter")})
    except PackageNotFoundError:
        rprint({"trpg-supporter": "dev"})


if __name__ == "__main__":
    cli()
