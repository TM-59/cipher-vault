# Copyright 2026 TM-59
"""Pure rules of Codebreaking. No web framework is touched here."""

import copy
from itertools import product
from typing import cast

import pytest

from cipher_vault.domain import (
    MAX_GUESSES,
    Code,
    Feedback,
    GuessScored,
    Round,
    RoundFinishedError,
    RoundState,
    Scoring,
)
from cipher_vault.domain.model import (
    CODE_LENGTH,
    CODE_TEXT,
    DIGIT_RANGE,
    DIGITS,
    MATCH_COUNTS,
    ROUND_WITHOUT_IDENTITY,
    THREE_EXACT,
    TOO_MANY_MATCHES,
    WRONG_LENGTH,
)

# secret, guess, exact, digit-only. Written by hand, not derived from the code.
SCORING = [
    ("0012", "0203", 1, 2),  # the documented example
    ("0012", "0012", 4, 0),  # all exact
    ("0012", "3345", 0, 0),  # none
    ("0012", "2100", 0, 4),  # every digit, no position
    ("0000", "0001", 3, 0),  # duplicates in the secret
    ("0001", "0000", 3, 0),  # duplicates in the guess: the extra 0 is not counted
    ("1122", "2211", 0, 4),
    ("1122", "1212", 2, 2),
    ("1122", "1111", 2, 0),  # two 1s exact; the other two have no 1 left to match
    ("0123", "1111", 1, 0),
    ("5555", "5550", 3, 0),
    ("0550", "5005", 0, 4),
    ("1234", "4321", 0, 4),
    ("1234", "1243", 2, 2),
    ("3300", "0033", 0, 4),
    ("2221", "1222", 2, 2),
]


def state_of(game: Round) -> RoundState:
    """Read the state afresh (a plain attribute read would be narrowed by the type checker)."""
    return game.state


@pytest.mark.parametrize(("secret", "guess", "exact", "partial"), SCORING)
def test_req_score_exact_first_then_the_rest_without_reuse(
    secret: str, guess: str, exact: int, partial: int
) -> None:
    """REQ-SCORE: the hand-written table of exact and digit-only matches holds."""
    feedback = Scoring.score(Code.parse(secret), Code.parse(guess))
    assert (feedback.exact, feedback.partial) == (exact, partial)


def test_req_score_every_pair_agrees_with_an_independent_count() -> None:
    """REQ-SCORE: scoring agrees with an independent count over sampled pairs."""
    codes = [Code((a, b, c, d)) for a, b, c, d in product(range(6), repeat=4)]
    assert len(codes) == len(DIGITS) ** CODE_LENGTH
    for secret in codes[::37]:  # 36 secrets against all 1296 guesses
        for guess in codes:
            feedback = Scoring.score(secret, guess)
            exact = sum(s == g for s, g in zip(secret.digits, guess.digits, strict=True))
            common = sum(min(secret.digits.count(d), guess.digits.count(d)) for d in range(6))
            assert (feedback.exact, feedback.partial) == (exact, common - exact)
            assert Scoring.score(guess, secret) == feedback  # scoring is symmetric
            assert feedback.solved is (secret == guess)


def test_req_score_only_codes_are_compared() -> None:
    """REQ-SCORE: scoring refuses values that are not codes."""
    with pytest.raises(TypeError):
        Scoring.score(Code.parse("0000"), cast("Code", "0000"))


@pytest.mark.parametrize(
    "bad",
    [
        (0, 1, 2),
        (0, 1, 2, 3, 4),
        (0, 1, 2, 6),
        (0, 1, 2, -1),
        (0, 1, 2, 1.0),
        (0, 1, 2, "3"),
        [0, 1, 2, 3],
        (True, 0, 0, 0),
    ],
)
def test_req_code_four_digits_from_zero_to_five(bad: object) -> None:
    """REQ-CODE: a code is four whole digits from 0 to 5."""
    with pytest.raises(ValueError, match=f"{WRONG_LENGTH}|{DIGIT_RANGE}"):
        Code(cast("tuple[int, int, int, int]", bad))


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "012",
        "01234",
        "0126",
        "01a2",
        "0 12",
        "-012",
        "".join(chr(ord("\N{FULLWIDTH DIGIT ZERO}") + n) for n in range(4)),  # full-width 0123
        "0.12",
        None,
        12,
    ],
)
def test_req_code_text_must_be_four_plain_digits(bad: object) -> None:
    """REQ-CODE: code text must be four plain ASCII digits."""
    with pytest.raises(ValueError, match=f"{CODE_TEXT}|{DIGIT_RANGE}"):
        Code.parse(cast("str", bad))


def test_req_code_is_an_immutable_value_with_repeats() -> None:
    """REQ-CODE: codes are frozen values and may repeat digits."""
    code = Code.parse("0055")
    assert code.digits == (0, 0, 5, 5)
    assert str(code) == "0055"
    assert code == Code((0, 0, 5, 5))
    assert hash(code) == hash(Code((0, 0, 5, 5)))
    field = "digits"
    with pytest.raises(AttributeError):
        setattr(code, field, (1, 1, 1, 1))  # a frozen value cannot be reassigned


@pytest.mark.parametrize("bad", [(-1, 0), (0, -1), (3, 2), (5, 0), (3, 1), (1.0, 0), ("1", 0)])
def test_req_code_feedback_values_are_possible_counts(bad: tuple[object, object]) -> None:
    """REQ-CODE: feedback counts must be possible."""
    with pytest.raises(ValueError, match=f"{MATCH_COUNTS}|{TOO_MANY_MATCHES}|{THREE_EXACT}"):
        Feedback(*cast("tuple[int, int]", bad))


def test_req_round_a_correct_guess_wins_and_the_event_hides_the_secret() -> None:
    """REQ-ROUND: a correct guess wins and the event does not carry the secret."""
    game = Round("r1", Code.parse("0012"))
    assert (state_of(game), game.turns_used, game.turns_left) == (RoundState.ACTIVE, 0, MAX_GUESSES)
    first = game.guess(Code.parse("0203"))
    assert first == GuessScored("r1", 1, Code.parse("0203"), Feedback(1, 2), RoundState.ACTIVE)
    won = game.guess(Code.parse("0012"))
    assert (won.turn, won.feedback, won.state) == (2, Feedback(4, 0), RoundState.WON)
    assert state_of(game) is RoundState.WON
    assert game.history == (first, won)
    assert not any("secret" in name for name in GuessScored.__dataclass_fields__)


def test_req_round_a_correct_eighth_guess_wins() -> None:
    """REQ-ROUND: a correct eighth guess still wins."""
    game = Round("r2", Code.parse("5432"))
    for _ in range(MAX_GUESSES - 1):
        assert game.guess(Code.parse("0000")).state is RoundState.ACTIVE
    last = game.guess(Code.parse("5432"))
    assert (last.turn, last.state) == (8, RoundState.WON)
    assert state_of(game) is RoundState.WON
    assert game.turns_left == 0


def test_req_round_an_incorrect_eighth_guess_exhausts() -> None:
    """REQ-ROUND: a wrong eighth guess exhausts the round."""
    game = Round("r3", Code.parse("5432"))
    events = [game.guess(Code.parse("0000")) for _ in range(MAX_GUESSES)]
    assert [event.turn for event in events] == list(range(1, 9))
    assert events[-2].state is RoundState.ACTIVE
    assert events[-1].state is RoundState.EXHAUSTED
    assert state_of(game) is RoundState.EXHAUSTED


@pytest.mark.parametrize("ending", [RoundState.WON, RoundState.EXHAUSTED])
def test_req_round_terminal_rounds_reject_and_do_not_change(ending: RoundState) -> None:
    """REQ-ROUND: finished rounds refuse guesses and stay unchanged."""
    game = Round("r4", Code.parse("1111"))
    if ending is RoundState.WON:
        game.guess(Code.parse("1111"))
    else:
        for _ in range(MAX_GUESSES):
            game.guess(Code.parse("2222"))
    assert state_of(game) is ending
    before = copy.deepcopy(game)
    with pytest.raises(RoundFinishedError):
        game.guess(Code.parse("1111"))
    assert game == before


@pytest.mark.parametrize("bad", ["0012", (0, 0, 1, 2), None, 12])
def test_req_round_invalid_input_consumes_no_turn(bad: object) -> None:
    """REQ-ROUND: a guess that is not a code uses no turn."""
    game = Round("r5", Code.parse("0012"))
    game.guess(Code.parse("5555"))
    before = copy.deepcopy(game)
    with pytest.raises(TypeError):
        game.guess(cast("Code", bad))
    assert game == before
    assert game.turns_used == 1


def test_req_round_identity_and_secret_are_required() -> None:
    """REQ-ROUND: identity and a hidden code are required."""
    with pytest.raises(ValueError, match=ROUND_WITHOUT_IDENTITY):
        Round("", Code.parse("0000"))
    with pytest.raises(TypeError):
        Round("r", cast("Code", "0000"))
    game = Round("r6", Code.parse("0000"))
    assert game.guess(Code.parse("1111")).round_id == "r6"


def test_req_round_same_guesses_give_the_same_history() -> None:
    """REQ-ROUND: the same guesses always give the same history."""
    guesses = [Code.parse(text) for text in ("0011", "2233", "4455", "0123")]
    histories = []
    for _ in range(2):
        game = Round("replay", Code.parse("0123"))
        histories.append(tuple(game.guess(code) for code in guesses))
    assert histories[0] == histories[1]
    assert histories[0][-1].state is RoundState.WON
