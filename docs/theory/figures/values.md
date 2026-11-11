# Measured values

Written by `make theory-figs` (scripts/theory_figs.py) from the domain itself. Do not edit by hand.
The last column is the relative error; where the theory column is 0 it is the absolute value.

| id | what is measured | measured | theory | error |
|---|---|---|---|---|
| `codes` | codes that pass validation, enumerated (theory 6^4) | 1296 | 1296 | 0.00e+00 |
| `codes-no-repeat` | of them, codes with four different digits (theory 6 x 5 x 4 x 3) | 360 | 360 | 0.00e+00 |
| `codes-rejected` | of five malformed inputs, how many raise ValueError (theory 5) | 5 | 5 | 0.00e+00 |
| `score-pairs` | pairs of secret and guess scored (theory 1296^2) | 1679616 | 1679616 | 0.00e+00 |
| `score-formula` | largest gap between the digit-only count and (multiset overlap - exact) over every pair (theory 0) | 0 | 0 | 0.00e+00 |
| `score-symmetric` | pairs whose feedback changes when secret and guess are swapped (theory 0) | 0 | 0 | 0.00e+00 |
| `score-example-exact` | exact matches for secret 0012, guess 0203 (the documented example: 1) | 1 | 1 | 0.00e+00 |
| `score-example-partial` | digit-only matches for the same pair (the documented example: 2) | 2 | 2 | 0.00e+00 |
| `feedback-kinds` | different feedbacks that occur over every pair (theory 14) | 14 | 14 | 0.00e+00 |
| `feedback-valid` | pairs (exact, digit-only) from 0..4 that Feedback accepts (theory 14: the same set) | 14 | 14 | 0.00e+00 |
| `feedback-three-one` | pairs scoring three exact and one digit-only (theory 0: impossible) | 0 | 0 | 0.00e+00 |
| `feedback-solved` | pairs scoring four exact (theory 1296: only a code against itself) | 1296 | 1296 | 0.00e+00 |
| `split-0000` | largest group of secrets sharing one feedback after the first guess 0000 (smaller is a better question) | 625 | 0 | 6.25e+02 |
| `split-0001` | largest group of secrets sharing one feedback after the first guess 0001 (smaller is a better question) | 317 | 0 | 3.17e+02 |
| `split-0011` | largest group of secrets sharing one feedback after the first guess 0011 (smaller is a better question) | 256 | 0 | 2.56e+02 |
| `split-0012` | largest group of secrets sharing one feedback after the first guess 0012 (smaller is a better question) | 276 | 0 | 2.76e+02 |
| `split-0123` | largest group of secrets sharing one feedback after the first guess 0123 (smaller is a better question) | 312 | 0 | 3.12e+02 |
| `first-fit-lost` | secrets the first-consistent-code strategy does not find within eight guesses (it is not good enough: not 0) | 6 | 0 | 6.00e+00 |
| `first-fit-mean` | its mean number of guesses over the secrets it does find | 5.7496124 | 0 | 5.75e+00 |
| `first-fit-wins` | secrets it finds within eight guesses, of 1296 | 1290 | 1296 | 4.63e-03 |
| `minimax-secrets` | secrets reached by the smallest-worst-group strategy (theory 1296: every one) | 1296 | 1296 | 0.00e+00 |
| `minimax-worst` | most guesses it needs over all 1296 secrets (the game allows 8, so every round can be won) | 6 | 0 | 6.00e+00 |
| `minimax-mean` | its mean number of guesses | 4.4969136 | 0 | 4.50e+00 |
| `round-eighth-wins` | state after a correct eighth guess (1 = won) | 1 | 1 | 0.00e+00 |
| `round-eighth-exhausts` | state after an incorrect eighth guess (1 = exhausted) | 1 | 1 | 0.00e+00 |
| `round-terminal-refuses` | a ninth guess raises RoundFinished (theory 1) | 1 | 1 | 0.00e+00 |
| `round-terminal-history` | guesses recorded after that refusal (theory 8: nothing was added) | 8 | 8 | 0.00e+00 |
| `round-invalid-free` | turns used after a guess that is not a Code (theory 0) | 0 | 0 | 0.00e+00 |
| `event-fields` | fields of GuessScored (round_id, turn, guess, feedback, state: 5) | 5 | 5 | 0.00e+00 |
| `event-secret-fields` | of them, fields that hold or name the secret (theory 0) | 0 | 0 | 0.00e+00 |
