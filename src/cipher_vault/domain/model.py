"""Codebreaking: the code and feedback values, scoring, and the round aggregate.

Standard library only. The hidden code is game state, not a credential.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum

CODE_LENGTH = 4
DIGITS = range(6)  # 0 through 5
MAX_GUESSES = 8


class RoundState(Enum):
    ACTIVE = "active"
    WON = "won"
    EXHAUSTED = "exhausted"


class RoundFinished(Exception):
    """A won or exhausted round accepts no further guess."""


@dataclass(frozen=True, slots=True)
class Code:
    """Four digits, each 0 through 5; repeats allowed."""

    digits: tuple[int, int, int, int]

    def __post_init__(self) -> None:
        if not isinstance(self.digits, tuple) or len(self.digits) != CODE_LENGTH:
            raise ValueError("a code has exactly four digits")
        if any(type(digit) is not int or digit not in DIGITS for digit in self.digits):
            raise ValueError("each digit is a whole number from 0 to 5")

    @staticmethod
    def parse(text: str) -> Code:
        """Read a code from text such as "0012". Anything else is rejected."""
        if not isinstance(text, str) or len(text) != CODE_LENGTH or not text.isascii():
            raise ValueError("a code is written as four digits")
        if not text.isdigit():
            raise ValueError("a code is written as four digits")
        a, b, c, d = (int(letter) for letter in text)
        return Code((a, b, c, d))

    def __str__(self) -> str:
        return "".join(str(digit) for digit in self.digits)


@dataclass(frozen=True, slots=True)
class Feedback:
    """Exact-position matches, and remaining matches of digit only."""

    exact: int
    partial: int

    def __post_init__(self) -> None:
        for count in (self.exact, self.partial):
            if type(count) is not int or count < 0:
                raise ValueError("match counts are non-negative whole numbers")
        if self.exact + self.partial > CODE_LENGTH:
            raise ValueError("at most four positions can match")
        if self.exact == CODE_LENGTH - 1 and self.partial == 1:
            raise ValueError("three exact matches leave no digit to match elsewhere")

    @property
    def solved(self) -> bool:
        return self.exact == CODE_LENGTH


class Scoring:
    """Pure domain service: exact matches first, then the rest without reuse."""

    @staticmethod
    def score(secret: Code, guess: Code) -> Feedback:
        if not isinstance(secret, Code) or not isinstance(guess, Code):
            raise TypeError("scoring compares two codes")
        exact = sum(s == g for s, g in zip(secret.digits, guess.digits, strict=True))
        left_secret = Counter(s for s, g in zip(secret.digits, guess.digits, strict=True) if s != g)
        left_guess = Counter(g for s, g in zip(secret.digits, guess.digits, strict=True) if s != g)
        partial = sum((left_secret & left_guess).values())
        return Feedback(exact, partial)


@dataclass(frozen=True, slots=True)
class GuessScored:
    """What the player learns from one guess. It never carries the secret."""

    round_id: str
    turn: int
    guess: Code
    feedback: Feedback
    state: RoundState


@dataclass(slots=True)
class Round:
    """Aggregate: identity, the secret, the ordered guesses and the derived state."""

    round_id: str
    secret: Code
    history: tuple[GuessScored, ...] = field(default=())

    def __post_init__(self) -> None:
        if not self.round_id:
            raise ValueError("a round needs an identity")
        if not isinstance(self.secret, Code):
            raise TypeError("the secret is a code")
        if len(self.history) > MAX_GUESSES:
            raise ValueError("a round holds at most eight guesses")

    @property
    def turns_used(self) -> int:
        return len(self.history)

    @property
    def turns_left(self) -> int:
        return MAX_GUESSES - len(self.history)

    @property
    def state(self) -> RoundState:
        if self.history and self.history[-1].feedback.solved:
            return RoundState.WON  # a correct eighth guess wins
        if len(self.history) >= MAX_GUESSES:
            return RoundState.EXHAUSTED
        return RoundState.ACTIVE

    def guess(self, code: Code) -> GuessScored:
        """Score one guess. Nothing changes when the round is over or the guess is not a code."""
        if self.state is not RoundState.ACTIVE:
            raise RoundFinished(f"the round is {self.state.value}")
        if not isinstance(code, Code):
            raise TypeError("a guess is a code")
        feedback = Scoring.score(self.secret, code)
        turn = len(self.history) + 1
        state = (
            RoundState.WON
            if feedback.solved
            else RoundState.EXHAUSTED
            if turn >= MAX_GUESSES
            else RoundState.ACTIVE
        )
        scored = GuessScored(self.round_id, turn, code, feedback, state)
        self.history += (scored,)
        return scored
