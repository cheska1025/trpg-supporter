from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, Mapping, Sequence

import click
from rich import print

# 세션은 "필요한 경우에만" 주입
try:
    from backend.app.db.session import AsyncSessionLocal  # type: ignore[import]
except Exception:  # pragma: no cover
    AsyncSessionLocal = None  # type: ignore[assignment]

# ---- 서비스 함수 동적 로드 (이름 변화에 내성) ------------------------------
# create/add
_CREATE_FN_NAMES: Sequence[str] = ("create_character", "add_character", "create", "add")
# list/get
_LIST_FN_NAMES: Sequence[str] = ("list_characters", "get_characters", "list", "get_all")


def _import_service_func(candidates: Sequence[str]) -> Callable[..., Any]:
    """
    backend.app.services.characters 모듈에서 후보 이름 중 첫 번째를 찾아 반환.
    mypy가 모듈 속성 유무를 정적으로 확정할 수 없으므로 Any로 취급한다.
    """
    from importlib import import_module

    mod = import_module("backend.app.services.characters")
    for name in candidates:
        if hasattr(mod, name):
            return getattr(mod, name)
    # 최종 실패 시 AttributeError
    raise AttributeError(
        f"None of {', '.join(candidates)} found in backend.app.services.characters"
    )


# 후에 실행 시점에서 실패하면 명확한 에러가 나도록, 여기서 즉시 해석은 하지 않는다.
# (명령 실행 시에 import 시도)
def _needs_db_param(func: Callable[..., Any]) -> bool:
    """
    함수 시그니처를 보고 DB 세션 인자를 요구하는지 판단.
    이름 기준: 'db', 'session', 'async_session' 중 하나가 존재하면 필요하다고 간주.
    타입 어노테이션이 AsyncSession이면 역시 필요로 간주.
    """
    try:
        sig = inspect.signature(func)
    except (TypeError, ValueError):
        return False

    for p in sig.parameters.values():
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
            name = p.name.lower()
            if name in {"db", "session", "async_session"}:
                return True
            # 타입 힌트 기반(선택적): 모듈 문자열에 'sqlalchemy'가 보이면 True로 본다
            ann = str(p.annotation)
            if "AsyncSession" in ann or "sqlalchemy" in ann.lower():
                return True
    return False


async def _call_maybe_async(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """코루틴 함수면 await, 동기 함수면 thread에서 실행."""
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return await asyncio.to_thread(func, *args, **kwargs)


def _filter_kwargs_for_func(
    func: Callable[..., Any], raw_kwargs: Mapping[str, Any]
) -> dict[str, Any]:
    """
    함수 시그니처에 존재하는 파라미터만 추려서 전달한다.
    (예: 서비스 함수가 name/clazz만 받고 level을 받지 않는 경우 대비)
    """
    try:
        sig = inspect.signature(func)
        allowed = set(sig.parameters.keys())
        return {k: v for k, v in raw_kwargs.items() if k in allowed}
    except (TypeError, ValueError):
        # 시그니처를 못 읽으면 그대로 전달(대부분 동작)
        return dict(raw_kwargs)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
cli = click.Group(name="trpg")


@cli.command("add")
@click.argument("name")
@click.argument("clazz")
@click.option("--level", default=1, type=int, show_default=True)
def add_cmd(name: str, clazz: str, level: int) -> None:
    """Add a new character (서비스 함수 이름/시그니처에 자동 적응)."""

    async def _run() -> None:
        # 1) 서비스 함수 로드
        create_fn = _import_service_func(_CREATE_FN_NAMES)

        # 2) 인자 정리
        payload = _filter_kwargs_for_func(create_fn, {"name": name, "clazz": clazz, "level": level})

        # 3) 세션 필요 여부에 따라 분기
        if _needs_db_param(create_fn) and AsyncSessionLocal is not None:
            async with AsyncSessionLocal() as db:  # type: ignore[misc]
                result = await _call_maybe_async(create_fn, db, **payload)
        else:
            result = await _call_maybe_async(create_fn, **payload)

        # 4) 출력 정규화
        if hasattr(result, "__dict__"):
            data = result.__dict__.copy()
            data.pop("_sa_instance_state", None)  # SQLAlchemy 객체 대비
            print(data)
        elif isinstance(result, dict):
            print(result)
        else:
            print({"result": result})

    asyncio.run(_run())


@cli.command("ls")
def ls_cmd() -> None:
    """List characters (서비스 함수 이름/시그니처/동기·비동기에 자동 적응)."""

    async def _run() -> None:
        list_fn = _import_service_func(_LIST_FN_NAMES)

        if _needs_db_param(list_fn) and AsyncSessionLocal is not None:
            async with AsyncSessionLocal() as db:  # type: ignore[misc]
                rows = await _call_maybe_async(list_fn, db)
        else:
            rows = await _call_maybe_async(list_fn)

        # rows 형식: list[ORM], list[dict], dict with 'items', etc. → 최대한 보편 처리
        out: list[dict[str, Any]] = []
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, dict)):
            for r in rows:
                if hasattr(r, "__dict__"):
                    d = r.__dict__.copy()
                    d.pop("_sa_instance_state", None)
                    out.append(d)
                elif isinstance(r, Mapping):
                    out.append(dict(r))
                else:
                    out.append({"value": r})
        elif isinstance(rows, Mapping):
            # 혹시 {"items": [...]} 형태인 경우
            items = rows.get("items")
            if isinstance(items, Sequence):
                for r in items:
                    if hasattr(r, "__dict__"):
                        d = r.__dict__.copy()
                        d.pop("_sa_instance_state", None)
                        out.append(d)
                    elif isinstance(r, Mapping):
                        out.append(dict(r))
                    else:
                        out.append({"value": r})
            else:
                out.append(dict(rows))
        else:
            out.append({"value": rows})

        # 가독성 최소 필드만 출력 시도
        simplified = []
        for d in out:
            if all(k in d for k in ("id", "name")):
                simplified.append({"id": d.get("id"), "name": d.get("name")})
            else:
                simplified.append(d)
        print(simplified)

    asyncio.run(_run())


__all__ = ["cli"]


if __name__ == "__main__":
    cli()
