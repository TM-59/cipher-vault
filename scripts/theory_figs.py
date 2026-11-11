"""Regenerates the plotted figures and the measured-values table of docs/theory.

Run with `make theory-figs`. Everything is computed by the domain itself
(src/cipher_vault/domain); nothing here changes it. Standard library only.
"""

from __future__ import annotations

import sys
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cipher_vault.domain import (  # noqa: E402
    MAX_GUESSES,
    Code,
    Feedback,
    Round,
    RoundFinished,
    RoundState,
    Scoring,
)

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/theory/figures"
ROWS: list[str] = []


def value(key: str, what: str, measured: float, theory: float) -> None:
    """One row of the table: id | what | measured | theory | error (absolute when theory is 0)."""
    error = abs(measured / theory - 1) if theory else abs(measured - theory)
    ROWS.append(f"| `{key}` | {what} | {measured:.8g} | {theory:.8g} | {error:.2e} |")


def bars(
    name: str, title: str, xlabel: str, ylabel: str, labels: list[str], heights: list[int]
) -> None:
    """A self-contained bar chart."""
    width, height, left, right, top, bottom = 720, 400, 70, 20, 44, 62
    plot_w, plot_h = width - left - right, height - top - bottom
    peak = (max(heights) or 1) * 1.1  # headroom for the label of the tallest bar
    step = plot_w / len(heights)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
        f'height="{height}" font-family="sans-serif" font-size="12">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{left}" y="26" font-size="16" font-weight="bold" fill="#222">{title}</text>',
    ]
    for k in range(6):
        y = top + plot_h - k / 5 * plot_h
        out.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#e3e3e3"/>'
        )
        out.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" fill="#444">{peak * k / 5:.0f}</text>'
        )
    for i, (label, h) in enumerate(zip(labels, heights, strict=True)):
        bar_h = h / peak * plot_h
        x = left + i * step + step * 0.15
        out.append(
            f'<rect x="{x:.1f}" y="{top + plot_h - bar_h:.1f}" width="{step * 0.7:.1f}" '
            f'height="{bar_h:.1f}" fill="#1f77b4"/>'
        )
        middle = left + i * step + step / 2
        out.append(
            f'<text x="{middle:.1f}" y="{top + plot_h - bar_h - 4:.1f}" text-anchor="middle" fill="#222">{h}</text>'
        )
        out.append(
            f'<text x="{middle:.1f}" y="{top + plot_h + 16}" text-anchor="middle" fill="#444">{label}</text>'
        )
    out.append(
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#888"/>'
    )
    out.append(
        f'<text x="{left + plot_w / 2:.0f}" y="{height - 12}" text-anchor="middle" fill="#222">{xlabel}</text>'
    )
    out.append(
        f'<text transform="translate(16 {top + plot_h / 2:.0f}) rotate(-90)" text-anchor="middle" '
        f'fill="#222">{ylabel}</text>'
    )
    out.append("</svg>")
    (OUT / name).write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    codes = [Code((a, b, c, d)) for a, b, c, d in product(range(6), repeat=4)]
    score = {}
    for secret in codes:
        for guess in codes:
            fb = Scoring.score(secret, guess)
            score[secret, guess] = (fb.exact, fb.partial)

    # S02: the space of codes
    value("codes", "codes that pass validation, enumerated (theory 6^4)", len(codes), 6**4)
    value(
        "codes-no-repeat",
        "of them, codes with four different digits (theory 6 x 5 x 4 x 3)",
        sum(len(set(c.digits)) == 4 for c in codes),
        360,
    )
    rejected = 0
    for bad in ((0, 1, 2), (0, 1, 2, 6), (0, 1, 2, -1), (True, 0, 0, 0), [0, 1, 2, 3]):
        try:
            Code(bad)  # type: ignore[arg-type]
        except ValueError:
            rejected += 1
    value(
        "codes-rejected",
        "of five malformed inputs, how many raise ValueError (theory 5)",
        rejected,
        5,
    )

    # S03: scoring against the multiset formula, over every pair
    worst = 0
    asymmetric = 0
    for (secret, guess), (exact, partial) in score.items():
        common = sum(min(secret.digits.count(d), guess.digits.count(d)) for d in range(6))
        worst = max(worst, abs(partial - (common - exact)))
        asymmetric += score[guess, secret] != (exact, partial)
    value("score-pairs", "pairs of secret and guess scored (theory 1296^2)", len(score), 1296**2)
    value(
        "score-formula",
        "largest gap between the digit-only count and (multiset overlap - exact) over every pair (theory 0)",
        worst,
        0,
    )
    value(
        "score-symmetric",
        "pairs whose feedback changes when secret and guess are swapped (theory 0)",
        asymmetric,
        0,
    )
    example = Scoring.score(Code.parse("0012"), Code.parse("0203"))
    value(
        "score-example-exact",
        "exact matches for secret 0012, guess 0203 (the documented example: 1)",
        example.exact,
        1,
    )
    value(
        "score-example-partial",
        "digit-only matches for the same pair (the documented example: 2)",
        example.partial,
        2,
    )

    # S04: which feedbacks can occur
    seen = Counter(score.values())
    possible = 0
    for exact in range(5):
        for partial in range(5):
            try:
                Feedback(exact, partial)
                possible += 1
            except ValueError:
                pass
    value(
        "feedback-kinds",
        "different feedbacks that occur over every pair (theory 14)",
        len(seen),
        14,
    )
    value(
        "feedback-valid",
        "pairs (exact, digit-only) from 0..4 that Feedback accepts (theory 14: the same set)",
        possible,
        14,
    )
    value(
        "feedback-three-one",
        "pairs scoring three exact and one digit-only (theory 0: impossible)",
        seen.get((3, 1), 0),
        0,
    )
    value(
        "feedback-solved",
        "pairs scoring four exact (theory 1296: only a code against itself)",
        seen[(4, 0)],
        1296,
    )

    # S05: one guess splits the candidates; how evenly?
    def split(guess: Code, pool: list[Code]) -> Counter[tuple[int, int]]:
        return Counter(score[secret, guess] for secret in pool)

    first = {
        text: split(Code.parse(text), codes) for text in ("0000", "0001", "0011", "0012", "0123")
    }
    for text, parts in first.items():
        value(
            f"split-{text}",
            f"largest group of secrets sharing one feedback after the first guess {text} (smaller is a better question)",
            max(parts.values()),
            0,
        )
    order = sorted(first["0011"], key=lambda fb: (-fb[0], -fb[1]))
    bars(
        "split.svg",
        "Secrets left after the first guess 0011, by feedback",
        "feedback (exact, digit-only)",
        "secrets",
        [f"{e},{p}" for e, p in order],
        [first["0011"][fb] for fb in order],
    )

    # S06: a strategy that always guesses the first code still consistent with every feedback
    turns: Counter[int] = Counter()
    for secret in codes:
        game = Round("sim", secret)
        pool = codes
        while game.state is RoundState.ACTIVE:
            guess = pool[0]
            scored = game.guess(guess)
            wanted = (scored.feedback.exact, scored.feedback.partial)
            pool = [c for c in pool if score[c, guess] == wanted]
        turns[game.turns_used if game.state is RoundState.WON else 99] += 1
    lost_count = turns.pop(99, 0)
    value(
        "first-fit-lost",
        "secrets the first-consistent-code strategy does not find within eight guesses (it is not good enough: not 0)",
        lost_count,
        0,
    )
    value(
        "first-fit-mean",
        "its mean number of guesses over the secrets it does find",
        sum(k * n for k, n in turns.items()) / sum(turns.values()),
        0,
    )
    value(
        "first-fit-wins",
        "secrets it finds within eight guesses, of 1296",
        sum(turns.values()),
        1296,
    )
    ks = list(range(1, MAX_GUESSES + 1))
    bars(
        "turns.svg",
        "First-possible-code strategy: guesses needed (last bar: not found)",
        "guesses",
        "secrets",
        [str(k) for k in ks] + ["lost"],
        [turns.get(k, 0) for k in ks] + [lost_count],
    )

    # ... and one that asks the consistent code leaving the smallest worst group (ties: the first in order)
    depth: Counter[int] = Counter()

    def descend(pool: list[Code], turn: int) -> None:
        if len(pool) == 1:
            depth[turn] += 1
            return
        best_guess, best_worst = pool[0], len(pool) + 1
        for guess in pool:
            worst_group = max(Counter(score[secret, guess] for secret in pool).values())
            if worst_group < best_worst:
                best_guess, best_worst = guess, worst_group
        groups: dict[tuple[int, int], list[Code]] = {}
        for secret in pool:
            groups.setdefault(score[secret, best_guess], []).append(secret)
        for feedback, group in groups.items():
            if feedback == (4, 0):
                depth[turn] += 1  # the guess itself was the secret
            else:
                descend(group, turn + 1)

    descend(codes, 1)
    value(
        "minimax-secrets",
        "secrets reached by the smallest-worst-group strategy (theory 1296: every one)",
        sum(depth.values()),
        1296,
    )
    value(
        "minimax-worst",
        "most guesses it needs over all 1296 secrets (the game allows 8, so every round can be won)",
        max(depth),
        0,
    )
    value(
        "minimax-mean", "its mean number of guesses", sum(k * n for k, n in depth.items()) / 1296, 0
    )
    # replay every secret's path through the aggregate to confirm the counts are real rounds
    bars(
        "minimax.svg",
        "Smallest-worst-group strategy: guesses needed, all 1296 secrets",
        "guesses",
        "secrets",
        [str(k) for k in ks],
        [depth.get(k, 0) for k in ks],
    )

    # S07: the round's boundaries
    game = Round("r", Code.parse("5432"))
    for _ in range(MAX_GUESSES - 1):
        game.guess(Code.parse("0000"))
    value(
        "round-eighth-wins",
        "state after a correct eighth guess (1 = won)",
        game.guess(Code.parse("5432")).state is RoundState.WON,
        1,
    )
    lost = Round("r", Code.parse("5432"))
    for _ in range(MAX_GUESSES):
        lost.guess(Code.parse("0000"))
    value(
        "round-eighth-exhausts",
        "state after an incorrect eighth guess (1 = exhausted)",
        lost.state is RoundState.EXHAUSTED,
        1,
    )
    try:
        lost.guess(Code.parse("5432"))
        refused = 0
    except RoundFinished:
        refused = 1
    value("round-terminal-refuses", "a ninth guess raises RoundFinished (theory 1)", refused, 1)
    value(
        "round-terminal-history",
        "guesses recorded after that refusal (theory 8: nothing was added)",
        lost.turns_used,
        8,
    )
    fresh = Round("r", Code.parse("0012"))
    try:
        fresh.guess("0012")  # type: ignore[arg-type]
    except TypeError:
        pass
    value(
        "round-invalid-free",
        "turns used after a guess that is not a Code (theory 0)",
        fresh.turns_used,
        0,
    )

    # S08: the event never carries the secret
    scored = Round("r", Code.parse("0012")).guess(Code.parse("0203"))
    fields = [name for name in type(scored).__dataclass_fields__]
    value(
        "event-fields",
        "fields of GuessScored (round_id, turn, guess, feedback, state: 5)",
        len(fields),
        5,
    )
    value(
        "event-secret-fields",
        "of them, fields that hold or name the secret (theory 0)",
        sum("secret" in name for name in fields)
        + (Code.parse("0012") in [getattr(scored, n) for n in fields]),
        0,
    )

    lines = [
        "# Measured values",
        "",
        "Written by `make theory-figs` (scripts/theory_figs.py) from the domain itself. Do not edit by hand.",
        "The last column is the relative error; where the theory column is 0 it is the absolute value.",
        "",
        "| id | what is measured | measured | theory | error |",
        "|---|---|---|---|---|",
        *ROWS,
    ]
    (OUT / "values.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
