from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from core.dice import roll
from core.initiative import Tracker
from core.log import append_markdown  # 백엔드/기존 호환용 (로컬 모드는 별도 구현 사용)

console = Console()

# --- 이니시 상태 영구 저장 위치 ---
STATE = Path.home() / ".trpg" / "init_state.json"
STATE.parent.mkdir(parents=True, exist_ok=True)

# --- 세션 로그 로컬 저장 기본 위치 (백엔드 미사용 시) ---
LOG_ROOT = Path("exports")
LOG_ROOT.mkdir(parents=True, exist_ok=True)


# ---------- 공통 유틸 ----------
def _tracker_snapshot(tr: Tracker) -> dict:
    """Tracker에 state()가 있든 없든 현재 상태를 dict로 반환."""
    try:
        return tr.state()  # 최신 엔진에는 state()가 존재
    except AttributeError:
        entries = getattr(tr, "entries", [])
        cursor = getattr(tr, "_cursor", -1)
        current = None
        if entries and isinstance(cursor, int) and 0 <= cursor < len(entries):
            current = getattr(entries[cursor], "name", None)
        return {
            "round": int(getattr(tr, "round", 1)),
            "current": current,
            "entries": [
                {
                    "name": getattr(e, "name", ""),
                    "value": int(getattr(e, "value", 0)),
                    "delayed": bool(getattr(e, "delayed", False)),
                    "effects": [
                        {
                            "name": getattr(fx, "name", ""),
                            "remain": int(getattr(fx, "remain_rounds", 0)),
                        }
                        for fx in (getattr(e, "effects", []) or [])
                    ],
                }
                for e in entries
            ],
        }


def _save_tracker(tr: Tracker) -> None:
    """Tracker 상태 저장: round, entries, current 커서까지."""
    st = _tracker_snapshot(tr)
    data = {
        "round": st["round"],
        "current": st["current"],  # 커서명 저장
        "entries": [
            {"name": e["name"], "value": int(e["value"]), "delayed": bool(e["delayed"])}
            for e in st["entries"]
        ],
    }
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_tracker() -> Tracker:
    """저장된 상태에서 Tracker 복원(라운드/엔트리/커서)."""
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

        # 커서 복원: 저장된 current 이름을 현재 엔트리 인덱스로 변환
        cur_name = data.get("current")
        if cur_name:
            try:
                idx = next(
                    i for i, e in enumerate(tr.entries) if e.name == cur_name and not e.delayed
                )
                tr._cursor = idx  # noqa: SLF001 - 내부 커서 복원
            except StopIteration:
                tr._cursor = -1
        else:
            tr._cursor = -1
    return tr


# ---------- 세션/캐릭터/세션로그 서비스 접근(필요 시) ----------
def _svc_session():
    """세션 상태 관련 서비스 임포트 (없으면 None 반환)."""
    try:
        from backend.app.services.session_state import (  # type: ignore
            close_session,
            create_session,
            current_session,
            set_current_session,
        )

        return {
            "current_session": current_session,
            "set_current_session": set_current_session,
            "create_session": create_session,
            "close_session": close_session,
        }
    except Exception as e:  # noqa: BLE001
        rprint({"error": f"백엔드 세션 서비스 불러오기 실패: {e}"})
        return None


def _svc_characters():
    """캐릭터 서비스 임포트 (없으면 None)."""
    try:
        from backend.app.services.characters import (  # type: ignore
            add_character,
            list_characters,
        )

        return {
            "add_character": add_character,
            "list_characters": list_characters,
        }
    except Exception as e:  # noqa: BLE001
        rprint({"error": f"백엔드 캐릭터 서비스 불러오기 실패: {e}"})
        return None


def _svc_session_log():
    """세션 로그 서비스 임포트 (없으면 None)."""
    try:
        from backend.app.services.session_log import (  # type: ignore
            append_session_log,
            export_session_log,
        )

        return {
            "append_session_log": append_session_log,
            "export_session_log": export_session_log,
        }
    except Exception as e:  # noqa: BLE001
        rprint({"warn": f"백엔드 세션 로그 서비스 불러오기 실패: {e} (로컬 모드로 대체)"})
        return None


def _log_paths(session_id: int | None) -> tuple[Path, Path]:
    """로컬 로그 파일 경로 리턴."""
    sid = session_id or 1
    return (LOG_ROOT / f"session_{sid}.md", LOG_ROOT / f"session_{sid}.json")


# ---------- 로컬 MD 기록 전용 유틸 ----------
_MD_SKELETON = "# Session Log\n\n## System\n\n## Narrative\n"


def _ensure_md_skeleton(md_path: Path) -> str:
    """세션 로그 MD 파일이 없으면 스켈레톤을 생성하고, 있으면 내용을 반환."""
    if md_path.exists():
        return md_path.read_text(encoding="utf-8")
    md_path.write_text(_MD_SKELETON, encoding="utf-8")
    return _MD_SKELETON


def _append_markdown_local(md_path: Path, channel: str, text: str, timestamp: str) -> None:
    """
    채널별 섹션에 안전하게 한 줄 추가.
    동일 라인이 이미 존재하면 추가하지 않음.
    """
    content = _ensure_md_skeleton(md_path)
    line = f"- {timestamp} {text}"

    # 중복 라인 방지
    if line in content:
        return

    # 섹션 찾아서 그 아래에 추가 (간단한 문자열 조작)
    if channel == "system":
        anchor = "## System"
    else:
        anchor = "## Narrative"

    parts = content.split(anchor)
    if len(parts) == 2:
        head, tail = parts
        # tail 시작에 개행 보정 후 라인 추가
        if not tail.startswith("\n"):
            tail = "\n" + tail
        new_tail = tail.rstrip() + "\n" + line + "\n"
        new_content = head + anchor + new_tail
        md_path.write_text(new_content, encoding="utf-8")
        return

    # 혹시 섹션이 없으면 스켈레톤 재작성 후 재귀
    md_path.write_text(_MD_SKELETON, encoding="utf-8")
    _append_markdown_local(md_path, channel, text, timestamp)


# ---------- CLI 루트 ----------
@click.group(
    help=(
        "TRPG Supporter CLI (MVP)\n\n"
        "주요 명령 예시:\n"
        '  trpg roll "2d6+3"\n'
        '  trpg session new "테스트 세션"\n'
        "  trpg char add Rogue\n"
        "  trpg init add Rogue 17\n"
        "  trpg init list\n"
        '  trpg slog add --channel system "라운드 시작"\n'
    )
)
def cli():
    """루트 그룹"""
    pass


# ---------- 주사위 ----------
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
    """주사위 굴림. --store 사용 시 DiceLog로 DB에 저장."""
    res = roll(formula, actor=actor, seed=seed, adv=adv, dis=dis)

    out = {
        "formula": res.formula,
        "rolls": res.rolls,
        "total": res.total,
        "actor": getattr(res, "actor", actor),
        "detail": getattr(res, "detail", {"rolls": res.rolls}),
    }

    if store:
        if not session_id:
            rprint({"error": "--store 사용 시 --session-id가 필요합니다."})
            return
        try:
            from backend.app.services.dice_log import save_dice_log  # type: ignore

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


# ---------- 이니시 ----------
@cli.group(help="이니시 명령군: add / update / remove / list / next / reset")
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
    snap = _tracker_snapshot(tr)
    rprint([{"name": e["name"], "value": e["value"]} for e in snap["entries"]])


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
    snap = _tracker_snapshot(tr)
    rprint([{"name": e["name"], "value": e["value"]} for e in snap["entries"]])


@init.command("remove", help="이니시 삭제 (예: trpg init remove Rogue)")
@click.argument("name")
def init_remove(name: str):
    tr = _load_tracker()
    ok = tr.remove(name)
    if not ok:
        rprint({"error": f"'{name}' 항목을 찾지 못했습니다."})
        return
    _save_tracker(tr)
    snap = _tracker_snapshot(tr)
    rprint([{"name": e["name"], "value": e["value"]} for e in snap["entries"]])


@init.command("list", help="현재 이니시 상태를 표로 출력")
def init_list():
    tr = _load_tracker()
    st = _tracker_snapshot(tr)

    table = Table(title=f"Initiative (Round {st['round']})")
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Value", justify="right", style="magenta")
    table.add_column("Delayed", justify="center", style="yellow")
    table.add_column("Effects", style="green")

    for i, e in enumerate(st["entries"], start=1):
        effects = ", ".join(f"{fx['name']}({fx['remain']})" for fx in e.get("effects", []))
        table.add_row(str(i), e["name"], str(e["value"]), "✅" if e["delayed"] else "", effects)

    console.print(table)


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


# ---------- 세션 ----------
@cli.group(help="세션 관리: new|open|close")
def session():
    pass


@session.command("new", help='새 세션 생성 (예: trpg session new "테스트 세션")')
@click.argument("title")
def session_new(title: str):
    svc = _svc_session()
    if not svc:
        return
    sess = svc["create_session"](title=title)
    svc["set_current_session"](sess["id"])
    rprint({"created": {"id": sess["id"], "title": sess["title"]}})


@session.command("open", help="기존 세션 열기 (현재 세션 지정)")
@click.argument("session_id", type=int)
def session_open(session_id: int):
    svc = _svc_session()
    if not svc:
        return
    svc["set_current_session"](session_id)
    rprint({"opened": session_id})


@session.command("close", help="현재 세션 닫기")
def session_close():
    svc = _svc_session()
    if not svc:
        return
    cur = svc["current_session"]()
    if not cur:
        rprint({"error": "열린 세션이 없습니다."})
        return
    svc["close_session"](cur["id"])
    rprint({"closed": cur["id"]})


# ---------- 캐릭터 ----------
@cli.group(help="캐릭터 관리: add|list (현재 세션 기준)")
def char():
    pass


@char.command("add", help="현재 세션에 캐릭터 추가 (예: trpg char add Rogue)")
@click.argument("name")
def char_add(name: str):
    sess = _svc_session()
    chars = _svc_characters()
    if not sess or not chars:
        return
    cur = sess["current_session"]()
    if not cur:
        rprint({"error": "먼저 세션을 열어주세요. (trpg session new|open)"})
        return
    chars["add_character"](session_id=cur["id"], name=name)
    rprint({"added": name})


@char.command("list", help="현재 세션의 캐릭터 목록")
def char_list():
    sess = _svc_session()
    chars = _svc_characters()
    if not sess or not chars:
        return
    cur = sess["current_session"]()
    if not cur:
        rprint({"error": "열린 세션이 없습니다."})
        return
    items = chars["list_characters"](session_id=cur["id"])
    table = Table(title=f"Characters in Session #{cur['id']} - {cur['title']}")
    table.add_column("Name", style="white")
    for it in items:
        table.add_row(it["name"])
    console.print(table)


# ---------- 세션 로그 ----------
@cli.group(name="slog", help="세션 로그: add|list|export")
def slog():
    pass


@slog.command("add", help='세션 로그 추가 (예: trpg slog add --channel system "라운드 시작")')
@click.option("--channel", type=click.Choice(["system", "narrative"]), required=True)
@click.argument("text")
@click.option("--session-id", type=int, default=None, help="로컬 모드에서 사용할 세션 ID")
def slog_add(channel: str, text: str, session_id: int | None):
    sess = _svc_session()
    logs = _svc_session_log()

    # --- 백엔드 모드: 서비스 사용 ---
    if sess and logs:
        cur = sess["current_session"]()
        if not cur:
            rprint({"error": "열린 세션이 없습니다."})
            return
        paths = logs["append_session_log"](session_id=cur["id"], channel=channel, text=text)
        rprint({"saved": paths})
        return

    # --- 로컬 모드: 파일(UTF-8)로 저장, 중복 방지 ---
    md_path, json_path = _log_paths(session_id)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # JSON 로드
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            data = []
    else:
        data = []

    # 중복 방지: 동일 (channel, text, timestamp) 라인 존재 시 skip
    if any(
        e.get("channel") == channel and e.get("text") == text and e.get("timestamp") == ts
        for e in data
    ):
        rprint({"info": "동일한 시간/채널/텍스트 로그가 이미 존재하여 건너뜁니다."})
        return

    # JSON append
    entry = {"channel": channel, "text": text, "timestamp": ts}
    data.append(entry)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown append (채널 섹션별, 중복 라인 방지)
    _append_markdown_local(md_path, channel, text, ts)

    rprint({"saved": {"md": str(md_path), "json": str(json_path)}})


def _load_local_json(json_path: Path) -> list[dict]:
    """로컬 JSON을 읽어 목록 반환. BOM/비BOM 모두 허용."""
    if not json_path.exists():
        return []
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return json.loads(json_path.read_text(encoding=enc))
        except Exception:
            continue
    return []


@slog.command("list", help="세션 로그 조회 (옵션: --channel, --since, --limit)")
@click.option("--channel", type=click.Choice(["system", "narrative"]), default=None)
@click.option("--since", type=str, default=None, help="YYYY-MM-DD 또는 YYYY-MM-DD HH:MM(:SS)")
@click.option("--limit", type=int, default=0, help="표시 개수 제한(0이면 전체)")
@click.option("--session-id", type=int, default=None, help="로컬 모드에서 사용할 세션 ID")
def slog_list(channel: str | None, since: str | None, limit: int, session_id: int | None):
    """세션 로그를 표로 출력합니다. 백엔드가 있으면 백엔드 export 후 파일을 읽고, 없으면 로컬 파일을 직접 읽습니다."""
    sess = _svc_session()
    logs = _svc_session_log()

    # 세션 결정
    session_id_eff: int
    if sess:
        cur = sess["current_session"]()
        if not cur:
            rprint({"error": "열린 세션이 없습니다."})
            return
        session_id_eff = cur["id"]
    else:
        session_id_eff = session_id or 1

    # 소스 선택: 백엔드가 있으면 export하여 최신 파일 읽기
    if sess and logs:
        paths = logs["export_session_log"](session_id=session_id_eff)
        json_path = Path(paths["json"])
        items = _load_local_json(json_path)
    else:
        _, json_path = _log_paths(session_id_eff)
        items = _load_local_json(json_path)

    # 필터링/정렬
    def _parse_ts(s: str) -> datetime | None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                pass
        return None

    if channel:
        items = [it for it in items if it.get("channel") == channel]

    if since:
        dt_since = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                dt_since = datetime.strptime(since, fmt)
                break
            except ValueError:
                continue
        if dt_since:
            items = [
                it
                for it in items
                if (_parse_ts(it.get("timestamp", "")) or datetime.min) >= dt_since
            ]
        else:
            rprint({"warn": f"--since 파싱 실패: {since}. 필터를 건너뜁니다."})

    items.sort(key=lambda it: _parse_ts(it.get("timestamp", "")) or datetime.min)

    if limit and limit > 0:
        items = items[-limit:]

    # 출력
    table = Table(title=f"Session Log (session #{session_id_eff})")
    table.add_column("Time", style="cyan")
    table.add_column("Channel", style="magenta")
    table.add_column("Text", style="white")

    for it in items:
        table.add_row(it.get("timestamp", ""), it.get("channel", ""), it.get("text", ""))

    console.print(table)


@slog.command("export", help="세션 로그 내보내기(.md/.json)")
@click.option("--session-id", type=int, default=None, help="로컬 모드에서 사용할 세션 ID")
def slog_export(session_id: int | None):
    sess = _svc_session()
    logs = _svc_session_log()

    if sess and logs:
        cur = sess["current_session"]()
        if not cur:
            rprint({"error": "열린 세션이 없습니다."})
            return
        paths = logs["export_session_log"](session_id=cur["id"])
        rprint({"exported": paths})
        return

    # 로컬 모드: 스켈레톤 보장 후 경로만 안내
    md_path, json_path = _log_paths(session_id)
    _ensure_md_skeleton(md_path)
    if not json_path.exists():
        json_path.write_text("[]", encoding="utf-8")
    rprint({"exported": {"md": str(md_path), "json": str(json_path)}})


# ---------- [Deprecated] 단일 로그 커맨드 ----------
@cli.command(help='[Deprecated] 세션 로그에 한 줄 추가 (예: trpg log --msg "세션 시작")')
@click.option("--msg", required=True, help="로그 텍스트")
@click.option("--out", default="./exports/session.md", show_default=True)
def log(msg: str, out: str):
    # 구버전 호환: 채널 구분 없이 narrative 섹션에만 append_markdown 사용
    append_markdown(out, msg)
    rprint({"saved": out})


# ---------- 버전 ----------
@cli.command(help="패키지 버전 표시(개발 중이면 dev)")
def version():
    from importlib.metadata import PackageNotFoundError, version

    try:
        rprint({"trpg-supporter": version("trpg-supporter")})
    except PackageNotFoundError:
        rprint({"trpg-supporter": "dev"})


if __name__ == "__main__":
    cli()
