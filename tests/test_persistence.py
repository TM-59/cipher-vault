# Copyright 2026 TM-59
"""The SQLite repository: persistence, atomic saves and revisions."""

import sqlite3
from typing import TYPE_CHECKING

import pytest

from cipher_vault.application.use_cases import RoundNotFoundError
from cipher_vault.composition import build_round_use_cases
from cipher_vault.domain import Code, Round, RoundState
from cipher_vault.infrastructure.repository import SQLiteRoundRepository

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.integration


def test_req_persistence_round_and_guess_history_survive_reopen(tmp_path: Path) -> None:
    """REQ-PERSISTENCE: the round and its guesses survive reopening the database."""
    database = tmp_path / "rounds.sqlite3"
    first = build_round_use_cases(database, lambda: "round-1", lambda: Code.parse("0012"))
    started = first.start.execute()
    assert started.secret is None

    first_event = first.guess.execute(started.round_id, Code.parse("0203"))
    reopened = build_round_use_cases(database, lambda: "unused", lambda: Code.parse("0012"))
    active = reopened.read.execute(started.round_id)
    assert active.state is RoundState.ACTIVE
    assert active.secret is None
    assert active.history == (first_event,)

    won = reopened.guess.execute(started.round_id, Code.parse("0012"))
    terminal = build_round_use_cases(
        database, lambda: "unused", lambda: Code.parse("0012")
    ).read.execute(started.round_id)
    assert won.state is RoundState.WON
    assert terminal.state is RoundState.WON
    assert terminal.secret == Code.parse("0012")
    assert terminal.history == (first_event, won)


def test_req_atomic_failed_guess_event_rolls_back_round_and_revision(tmp_path: Path) -> None:
    """REQ-ATOMIC: a failed event insert rolls back the round and revision."""
    database = tmp_path / "rounds.sqlite3"
    use_cases = build_round_use_cases(database, lambda: "round-1", lambda: Code.parse("0012"))
    started = use_cases.start.execute()
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            """CREATE TRIGGER reject_guess BEFORE INSERT ON round_guesses
               BEGIN SELECT RAISE(ABORT, 'guess rejected'); END"""
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(sqlite3.IntegrityError, match="guess rejected"):
        use_cases.guess.execute(started.round_id, Code.parse("0203"))

    record = build_round_use_cases(database).read.execute(started.round_id)
    assert record.state is RoundState.ACTIVE
    assert record.turns_used == 0
    assert record.history == ()
    assert record.secret is None


def test_req_revision_stale_snapshot_cannot_append_a_guess(tmp_path: Path) -> None:
    """REQ-REVISION: a stale snapshot cannot append a guess."""
    repository = SQLiteRoundRepository(tmp_path / "rounds.sqlite3")
    repository.add(Round("round-stale", Code.parse("0012")))
    first = repository.get("round-stale")
    stale = repository.get("round-stale")
    assert first is not None
    assert stale is not None

    first_event = first.round.guess(Code.parse("0203"))
    assert repository.save(first.round, first_event, first.revision)
    stale_event = stale.round.guess(Code.parse("0000"))
    assert not repository.save(stale.round, stale_event, stale.revision)

    stored = repository.get("round-stale")
    assert stored is not None
    assert stored.revision == 1
    assert stored.events == (first_event,)


def test_req_persistence_missing_round_is_not_a_success_shaped_result(
    tmp_path: Path,
) -> None:
    """REQ-PERSISTENCE: a missing round is None, not an empty record."""
    use_cases = build_round_use_cases(tmp_path / "rounds.sqlite3")

    with pytest.raises(RoundNotFoundError):
        use_cases.read.execute("missing")
