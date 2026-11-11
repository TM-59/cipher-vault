# Cipher Vault

A codebreaking puzzle built with Python and FastAPI, one small milestone at a time.
M2 implements the rules as a pure domain; storage and the browser game follow later.

The rules: find a four-digit code in eight guesses. Digits 0-5 may repeat;
feedback reports exact matches and digit-only matches. See [the domain design](docs/domain.md)
and [verification scope](docs/requirements.md).

**Theory handbook**: [docs/theory/](docs/theory/README.md) — 8 statements (the language, the code value,
scoring, the possible feedbacks, why eight guesses are enough, the round, one guess step by step, the
dependency rule), each with its rule, assumptions, derivation, code, tests and a figure. `make theory-figs`
regenerates the figures and the measured values; `make theory-check` checks the coverage table.

## Run the scaffold

Install Python 3.14 and [uv](https://docs.astral.sh/uv/), then:

```sh
make sync
make check
make serve
```

`GET http://localhost:8000/health` returns `{"status":"ok"}`. The server is local.
No game screen or database exists yet; M3 adds SQLite and M4 adds the browser game.
The rules can be tried from Python without FastAPI:

```sh
PYTHONPATH=src python3 -c "
from cipher_vault.domain import Code, Round
game = Round('demo', Code.parse('0012'))
print(game.guess(Code.parse('0203')).feedback)  # one exact, two digit-only
print(game.guess(Code.parse('0012')).state)
"
```
 No screenshots are claimed before a playable screen exists.

`make test` runs the unit checks. Local JUnit and summary files stay under ignored
`test-results/`. Pull requests run lint, typing, architecture and unit checks only.
