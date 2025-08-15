from __future__ import annotations

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
    """Tracker 상태를 최소 정보(round, entries)로 저장."""
    st = tr.state()  # {"round", "current", "entries":[{name,value,delayed,effects:[...]}]}
    data = {
        "round": st["round"],
        "entries": [
            {"name": e["name"], "value": int(e["value"]), "delayed": bool(e["delayed"])}
            for e in st["entries"]
        ],
    }
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_tracker() -> Tracker:
    """저장된 상태에서 Tracker 복원(라운드/엔트리만). 커서는 새 라운드 시작 상태."""
    tr = Tracker()
    if STATE.exists():
        data = json.loads(STATE.read_text(encoding="utf-8"))
        tr.round = int(data.get("round", 1))
        for it in data.get("entries", []):
            name = str(it["name"])
            value = int(it["value"])
            tr.add(name, value)
            if bool(it.get("delayed", False)):
                tr.delay(name)
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
    """루트 그룹"""
    pass


# ---- 주사위 ----
@cli.command("roll", help='주사위 굴림 (예: trpg roll "2d6+3")')
@click.argument("formula")
@click.option("--actor", help="굴린 주체명(표시용)")
@click.option("--seed", type=int, help="랜덤 시드(재현성)")
@click.option("--adv", is_flag=True, help="어드밴티지")
@click.option("--dis", is_flag=True, help="디스어드밴티지")
@click.option("--store", is_flag=True, help="DB에 DiceLog 저장")
@click.option("--session-id", type=int, help="저장 시 대상 세션 ID")
@click.option("--roller-id", type=int, help="저장 시 사용자(roller) ID")
def rollcmd(
    formula: str,
    actor: str | None,
    seed: int | None,
    adv: bool,
    dis: bool,
    store: bool,
    session_id: int | None,
    roller_id: int | None,
):
    """
    주사위 굴림. --store 사용 시 DiceLog로 DB에 저장합니다.
    """
    # core.dice.roll(v1) 시그니처에 맞춰 전달
    res = roll(formula, actor=actor, seed=seed, adv=adv, dis=dis)

    out = {
        "formula": res.formula,
        "rolls": res.rolls,
        "total": res.total,
        "actor": getattr(res, "actor", actor),
        "detail": getattr(res, "detail", {"rolls": res.rolls}),
    }

    # --store 지정 시 DB 저장
    if store:
        if not session_id:
            rprint({"error": "--store 사용 시 --session-id가 필요합니다."})
            return
        try:
            from backend.app.services.dice_log import save_dice_log

            new_id = save_dice_log(
                session_id=session_id,
                roller_id=roller_id,
                total=res.total,
                formula=res.formula,
                detail=out["detail"],
            )
            out["saved_id"] = new_id
        except Exception as e:  # noqa: BLE001
            out["db_error"] = str(e)

    rprint(out)


# ---- 이니시 ----
@cli.group(help="이니시 명령군: add / update / remove / next / reset")
def init():
    pass


@init.command("add", help="이니시 등록 (예: trpg init add Rogue 17)")
@click.argument("name")
@click.argument("value", type=int)
def init_add(name: str, value: int):
    tr = _load_tracker()
    try:
        tr.add(name, value)
    except ValueError as e:  # 이미 존재
        rprint({"error": str(e)})
        return
    _save_tracker(tr)
    rprint([{"name": e["name"], "value": e["value"]} for e in tr.state()["entries"]])


@init.command("update", help="이니시 수치 수정 (예: trpg init update Rogue 14)")
@click.argument("name")
@click.argument("value", type=int)
def init_update(name: str, value: int):
    tr = _load_tracker()
    try:
        tr.update(name, value)
    except ValueError as e:
        rprint({"error": str(e)})
        return
    _save_tracker(tr)
    rprint([{"name": e["name"], "value": e["value"]} for e in tr.state()["entries"]])


@init.command("remove", help="이니시 삭제 (예: trpg init remove Rogue)")
@click.argument("name")
def init_remove(name: str):
    tr = _load_tracker()
    ok = tr.remove(name)
    if not ok:
        rprint({"error": f"'{name}' 항목을 찾지 못했습니다."})
        return
    _save_tracker(tr)
    rprint([{"name": e["name"], "value": e["value"]} for e in tr.state()["entries"]])


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
