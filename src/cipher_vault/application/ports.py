"""Persistence ports used by the application layer."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from cipher_vault.domain import GuessScored, Round


@dataclass(frozen=True, slots=True)
class RoundRecord:
    """A stored round with its ordered guess events and the revision it was read at."""

    round: Round
    events: tuple[GuessScored, ...]
    revision: int


class RoundRepository(Protocol):
    """Port for storing rounds; `save` succeeds only for the revision that was read."""

    def add(self, round_: Round) -> None:
        """Store a new round at revision 0 with no guesses."""

    def get(self, round_id: str) -> RoundRecord | None:
        """Return the round, its events and revision, or None when it does not exist."""

    def save(self, round_: Round, event: GuessScored, expected_revision: int) -> bool:
        """Write the round and append `event` if the revision is unchanged."""
