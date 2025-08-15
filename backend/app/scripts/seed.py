from __future__ import annotations

from backend.app.core.db import session_scope
from backend.app.models import (
    Character,
    DiceLog,
    Encounter,
    Initiative,
    LogEntry,
    Session,
    User,
)


def main():
    with session_scope() as s:
        gm = User(name="GM", role="GM")
        player = User(name="Rogue", role="Player")
        s.add_all([gm, player])
        s.flush()

        sess = Session(title="Demo Session", gm_id=gm.id, status="open")
        s.add(sess)
        s.flush()

        ch = Character(
            owner_id=player.id,
            session_id=sess.id,
            name="Rogue",
            clazz="Rogue",
            stats={"hp": 10, "str": 12, "dex": 16},
        )
        s.add(ch)
        s.flush()

        enc = Encounter(session_id=sess.id, round=1, notes="Prologue fight")
        s.add(enc)
        s.flush()

        ini = Initiative(encounter_id=enc.id, actor_name="Rogue", value=17, order=1)
        s.add(ini)

        dlog = DiceLog(
            session_id=sess.id,
            roller_id=player.id,
            formula="1d20+5",
            detail={"rolls": [12], "bonus": 5},
            total=17,
        )
        s.add(dlog)

        log = LogEntry(session_id=sess.id, category="system", message="Seed complete")
        s.add(log)

    print("Seed OK")


if __name__ == "__main__":
    main()
