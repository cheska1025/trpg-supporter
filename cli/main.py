import click
from rich import print as rprint

from core.dice import roll
from core.initiative import Tracker
from core.log import append_markdown

_tracker = Tracker()


@click.group()
def cli():
    """TRPG Supporter CLI (MVP 스텁)"""


@cli.command()
@click.argument("formula")
def rollcmd(formula: str):
    """주사위 굴림: e.g. trpg rollcmd "2d6+3" """
    res = roll(formula)
    rprint({"formula": res.formula, "rolls": res.rolls, "total": res.total})


@cli.group()
def init():
    """이니시 명령군"""


@init.command("add")
@click.argument("name")
@click.argument("value", type=int)
def init_add(name: str, value: int):
    _tracker.add(name, value)
    rprint([{"name": e.name, "value": e.value} for e in _tracker.entries])


@init.command("next")
def init_next():
    cur = _tracker.next()
    rprint({"round": _tracker.round, "current": None if cur is None else cur.name})


@cli.command()
@click.option("--msg", required=True, help="로그 텍스트")
@click.option("--out", default="./exports/session.md", show_default=True)
def log(msg: str, out: str):
    """세션 로그 추가 및 md로 누적"""
    append_markdown(out, msg)
    rprint({"saved": out})


@cli.command()
def version():
    from importlib.metadata import PackageNotFoundError, version

    try:
        rprint({"trpg-supporter": version("trpg-supporter")})
    except PackageNotFoundError:
        rprint({"trpg-supporter": "dev"})
