# cli/main.py
from __future__ import annotations

import json
import os
from pathlib import Path

import click

from core.dice import roll as dice_roll
from core.log import LogManager  # append_markdown은 호환용으로만 임포트

APP_DIRNAME = ""  # 비워두면 바로 TRPG_HOME 루트 사용
SESSION_FILE = "session.json"
INIT_FILE = "initiative.json"


def trpg_home() -> Path:
    base = os.getenv("TRPG_HOME")
    if base:
        root = Path(base)
    else:
        root = Path.home() / ".trpg"
    d = root / APP_DIRNAME if APP_DIRNAME else root
    d.mkdir(parents=True, exist_ok=True)
    return d


def session_path() -> Path:
    return trpg_home() / SESSION_FILE


def init_path() -> Path:
    return trpg_home() / INIT_FILE


def load_json(p: Path, default):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default


def save_json(p: Path, data) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@click.group()
def cli():
    """TRPG CLI (MVP) — 세션/전투/로그/내보내기"""


# -------------------------------------------------------------------
# session
# -------------------------------------------------------------------
@cli.group()
def session():
    """세션 관리"""


@session.command("new")
@click.argument("title", nargs=-1)
def session_new(title):
    """새 세션 생성"""
    title = " ".join(title) if title else "Untitled"
    data = {
        "title": title,
        "status": "open",
    }
    save_json(session_path(), data)
    click.echo(f"Created session: {title}")


@session.command("close")
def session_close():
    """세션 종료"""
    data = load_json(session_path(), {})
    if not data:
        raise click.UsageError("No session found. Run: trpg session new <title>")
    data["status"] = "closed"
    save_json(session_path(), data)
    click.echo("Session closed")


# -------------------------------------------------------------------
# enc (encounter)
# -------------------------------------------------------------------
@cli.group()
def enc():
    """전투 관리 (Encounter)"""


@enc.command("start")
def enc_start():
    """전투 시작 (이니시 초기화)"""
    s = load_json(session_path(), {})
    if not s:
        raise click.UsageError("No session found. Run: trpg session new <title> first.")
    init = {
        "order": [],  # [{name, value, delayed}]
        "index": 0,
        "round": 1,
    }
    save_json(init_path(), init)
    click.echo("Encounter started (round=1)")


@enc.command("end")
def enc_end():
    """전투 종료"""
    p = init_path()
    if p.exists():
        p.unlink()
    click.echo("Encounter ended")


# -------------------------------------------------------------------
# init (initiative)
# -------------------------------------------------------------------
@cli.group()
def init():
    """이니시 관리"""


@init.command("add")
@click.argument("name")
@click.argument("value", type=int)
def init_add(name, value):
    """이니시에 참가자 추가"""
    init = load_json(init_path(), None)
    if init is None:
        raise click.UsageError("No encounter. Run: trpg enc start")
    init["order"].append({"name": name, "value": int(value), "delayed": False})
    # value 내림차순, 입력 순 유지(안정 정렬)
    init["order"].sort(key=lambda e: (-e["value"]))
    save_json(init_path(), init)
    click.echo(f"Added: {name} ({value})")


@init.command("list")
def init_list():
    """현재 이니시 순서 출력"""
    init = load_json(init_path(), None)
    if init is None:
        raise click.UsageError("No encounter. Run: trpg enc start")
    for i, e in enumerate(init["order"], 1):
        mark = "*" if i - 1 == init["index"] else " "
        dl = "(D)" if e.get("delayed") else ""
        click.echo(f"{mark} {e['name']} {e['value']} {dl}")
    click.echo(f"round={init['round']} index={init['index']}")


@init.command("next")
def init_next():
    """다음 턴으로 진행 (라운드 증가 포함)"""
    init = load_json(init_path(), None)
    if init is None:
        raise click.UsageError("No encounter. Run: trpg enc start")
    if not init["order"]:
        click.echo("No entries")
        return
    init["index"] += 1
    if init["index"] >= len(init["order"]):
        init["index"] = 0
        init["round"] += 1
    save_json(init_path(), init)
    click.echo(f"Turn -> index={init['index']} round={init['round']}")


@init.command("delay")
@click.argument("name")
def init_delay(name):
    """대상을 보류로 표시 (현재 턴이면 다음으로 진행)"""
    init = load_json(init_path(), None)
    if init is None:
        raise click.UsageError("No encounter. Run: trpg enc start")
    idx = init["index"]
    for i, e in enumerate(init["order"]):
        if e["name"] == name and not e.get("delayed"):
            e["delayed"] = True
            if i == idx:
                # 현재 턴 보류 시 즉시 다음
                init["index"] += 1
                if init["index"] >= len(init["order"]):
                    init["index"] = 0
                    init["round"] += 1
            save_json(init_path(), init)
            click.echo(f"Delayed: {name}")
            return
    click.echo(f"Not found or already delayed: {name}")


@init.command("return")
@click.argument("name")
def init_return(name):
    """보류된 대상을 같은 라운드 꼬리로 재진입"""
    init = load_json(init_path(), None)
    if init is None:
        raise click.UsageError("No encounter. Run: trpg enc start")
    order = init["order"]
    idx = init["index"]
    for i, e in enumerate(order):
        if e["name"] == name and e.get("delayed"):
            e["delayed"] = False
            ent = order.pop(i)
            order.append(ent)  # 꼬리로 이동
            if i < idx:
                init["index"] -= 1
            init["index"] %= len(order)
            save_json(init_path(), init)
            click.echo(f"Returned: {name}")
            return
    click.echo(f"Not found or not delayed: {name}")


# -------------------------------------------------------------------
# roll
# -------------------------------------------------------------------
@cli.command("roll")
@click.argument("formula")
@click.option("--as", "actor", default=None, help="굴림 주체 이름")
def cmd_roll(formula, actor):
    """주사위 굴림"""
    s = load_json(session_path(), {})
    if not s:
        raise click.UsageError("No session found. Run: trpg session new <title> first.")
    res = dice_roll(formula)
    click.echo(f"Roll {formula} -> total={res['total']} detail={res['detail']}")
    # 로그 기록
    lm = LogManager(s.get("title", "Session"))
    lm.append_system(event="dice", data={"actor": actor, "formula": formula, **res})
    # 내보내기는 별도 export 명령에서 수행


# -------------------------------------------------------------------
# log
# -------------------------------------------------------------------
@cli.group()
def log():
    """로그 기록"""


@log.command("add")
@click.argument("text", nargs=-1)
@click.option("--scene", default=None)
def log_add(text, scene):
    """내러티브 로그 추가"""
    s = load_json(session_path(), {})
    if not s:
        raise click.UsageError("No session found. Run: trpg session new <title> first.")
    text = " ".join(text)
    lm = LogManager(s.get("title", "Session"))
    lm.append_narrative(text=text, scene=scene)
    click.echo("Narrative logged")


# -------------------------------------------------------------------
# export
# -------------------------------------------------------------------
@cli.command("export")
@click.argument("fmt", type=click.Choice(["md", "json"]))
def export_cmd(fmt):
    """로그 내보내기 (md/json)"""
    s = load_json(session_path(), {})
    if not s:
        raise click.UsageError("No session found. Run: trpg session new <title> first.")
    lm = LogManager(s.get("title", "Session"))
    # 세션 실행 중 누적된 LogManager 인스턴스가 아니라면?
    # 간단화를 위해 이번 커맨드에서는 빈 로그도 파일 생성만 보장
    # (실전에서는 상태 보관/주입이 필요)
    path = lm.export(fmt)
    click.echo(f"Exported -> {path}")
