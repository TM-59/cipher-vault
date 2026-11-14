import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from cipher_vault.application.ports import RoundRecord
from cipher_vault.domain import Code, GuessScored, Round

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rounds (
    round_id TEXT PRIMARY KEY NOT NULL,
    secret_code TEXT NOT NULL CHECK (length(secret_code) = 4),
    revision INTEGER NOT NULL DEFAULT 0 CHECK (revision >= 0)
);
CREATE TABLE IF NOT EXISTS round_guesses (
    round_id TEXT NOT NULL REFERENCES rounds(round_id) ON DELETE CASCADE,
    turn INTEGER NOT NULL CHECK (turn BETWEEN 1 AND 8),
    guess TEXT NOT NULL CHECK (length(guess) = 4),
    exact INTEGER NOT NULL CHECK (exact BETWEEN 0 AND 4),
    partial INTEGER NOT NULL CHECK (partial BETWEEN 0 AND 4),
    state TEXT NOT NULL CHECK (state IN ('active', 'won', 'exhausted')),
    PRIMARY KEY (round_id, turn)
);
"""


class SQLiteRoundRepository:
    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        if self._path == ":memory:":
            raise ValueError("SQLiteRoundRepository requires a file-backed database")
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(_SCHEMA)

    def add(self, round_: Round) -> None:
        with self._connection() as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO rounds (round_id, secret_code) VALUES (?, ?)",
                    (round_.round_id, str(round_.secret)),
                )

    def get(self, round_id: str) -> RoundRecord | None:
        with self._connection() as connection:
            with connection:
                connection.execute("BEGIN")
                row = connection.execute(
                    "SELECT round_id, secret_code, revision FROM rounds WHERE round_id = ?",
                    (round_id,),
                ).fetchone()
                if row is None:
                    return None
                round_ = Round(
                    cast(str, row["round_id"]),
                    Code.parse(cast(str, row["secret_code"])),
                )
                events = tuple(
                    self._replay(round_, guess_row)
                    for guess_row in connection.execute(
                        """SELECT turn, guess, exact, partial, state FROM round_guesses
                           WHERE round_id = ? ORDER BY turn""",
                        (round_id,),
                    )
                )
                revision = cast(int, row["revision"])
                if len(events) != revision:
                    raise ValueError("stored revision does not match the guess history")
                return RoundRecord(round_, events, revision)

    def save(self, round_: Round, event: GuessScored, expected_revision: int) -> bool:
        if (
            event.round_id != round_.round_id
            or not round_.history
            or round_.history[-1] != event
            or event.turn != expected_revision + 1
        ):
            raise ValueError("guess event does not match the round transition")
        with self._connection() as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                changed = connection.execute(
                    """UPDATE rounds SET revision = revision + 1
                       WHERE round_id = ? AND revision = ?""",
                    (round_.round_id, expected_revision),
                ).rowcount
                if changed == 0:
                    return False
                connection.execute(
                    """INSERT INTO round_guesses
                       (round_id, turn, guess, exact, partial, state)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        event.round_id,
                        event.turn,
                        str(event.guess),
                        event.feedback.exact,
                        event.feedback.partial,
                        event.state.value,
                    ),
                )
        return True

    @staticmethod
    def _replay(round_: Round, row: sqlite3.Row) -> GuessScored:
        event = round_.guess(Code.parse(cast(str, row["guess"])))
        if (
            event.turn != row["turn"]
            or event.feedback.exact != row["exact"]
            or event.feedback.partial != row["partial"]
            or event.state.value != row["state"]
        ):
            raise ValueError("stored guess event does not match the round rules")
        return event

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=5)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
        finally:
            connection.close()
