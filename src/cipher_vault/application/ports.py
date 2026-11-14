from dataclasses import dataclass
from typing import Protocol

from cipher_vault.domain import GuessScored, Round


@dataclass(frozen=True, slots=True)
class RoundRecord:
    round: Round
    events: tuple[GuessScored, ...]
    revision: int


class RoundRepository(Protocol):
    def add(self, round_: Round) -> None: ...

    def get(self, round_id: str) -> RoundRecord | None: ...

    def save(self, round_: Round, event: GuessScored, expected_revision: int) -> bool: ...
