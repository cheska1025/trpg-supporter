import json
from pathlib import Path

import click
from rich import print as rprint

from core.dice import roll
from core.initiative import Tracker
from core.log import append_markdown

# --- 이니시 상태 영구 저장 위치 ---
STATE = Path.home() / ".trpg" / "init_state.json"
STATE.parent.mkdir(parents=True, exist_ok=True)


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
        '  trpg log --msg "세션 시작"\n'
    )
)
def cli():
    pass


# ---- 주사위 ----
@cli.command("roll", help='주사위 굴림 (예: trpg roll "2d6+3")')
@click.argument("formula")
def rollcmd(formula: str):
    res = roll(formula)
    rprint({"formula": res.formula, "rolls": res.rolls, "total": res.total})


# ---- 이니시 ----
@cli.group(help="이니시 명령군: add / update / remove / next")
def init():
    pass


@init.command("add", help="이니시 등록 (예: trpg init add Rogue 17)")
@click.argument("name")
@click.argument("value", type=int)
def init_add(name: str, value: int):
    tr = _load_tracker()
    tr.add(name, value)
    _save_tracker(tr)
    rprint([{"name": e.name, "value": e.value} for e in tr.entries])


@init.command("update", help="이니시 수치 수정 (예: trpg init update Rogue 14)")
@click.argument("name")
@click.argument("value", type=int)
def init_update(name: str, value: int):
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
    rprint([{"name": e.name, "value": e.value} for e in tr.entries])


@init.command("remove", help="이니시 삭제 (예: trpg init remove Rogue)")
@click.argument("name")
def init_remove(name: str):
    tr = _load_tracker()
    before = len(tr.entries)
    tr.entries = [e for e in tr.entries if e.name != name]
    after = len(tr.entries)
    if before == after:
        rprint({"error": f"'{name}' 항목을 찾지 못했습니다."})
        return
    # 삭제 후 인덱스/라운드 안전 보정
    if tr.idx >= len(tr.entries):
        tr.idx = 0 if tr.entries else 0
    _save_tracker(tr)
    rprint([{"name": e.name, "value": e.value} for e in tr.entries])


@init.command("next", help="다음 턴으로 진행(라운드 자동 증가)")
def init_next():
    tr = _load_tracker()
    cur = tr.next()
    _save_tracker(tr)
    rprint({"round": tr.round, "current": None if cur is None else cur.name})


@init.command("reset", help="이니시 상태 초기화")
def init_reset():
    if STATE.exists():
        STATE.unlink()
    rprint({"reset": True})


# ---- 로그 ----
@cli.command(help='세션 로그 추가 및 md로 누적 (예: trpg log --msg "세션 시작")')
@click.option("--msg", required=True, help="로그 텍스트")
@click.option("--out", default="./exports/session.md", show_default=True)
def log(msg: str, out: str):
    append_markdown(out, msg)
    rprint({"saved": out})


# ---- 버전 ----
@cli.command(help="패키지 버전 표시(개발 중이면 dev)")
def version():
    from importlib.metadata import PackageNotFoundError, version

    try:
        rprint({"trpg-supporter": version("trpg-supporter")})
    except PackageNotFoundError:
        rprint({"trpg-supporter": "dev"})


if __name__ == "__main__":
    cli()
