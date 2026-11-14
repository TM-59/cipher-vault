# Cipher Vault

A codebreaking puzzle built with Python and FastAPI, one small milestone at a time.
M3 adds application use cases and file-backed SQLite persistence to the pure M2 domain.

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

`GET http://localhost:8000/health` returns `{"status":"ok"}`. The server is local;
gameplay use cases are currently exposed through Python, not HTTP endpoints. SQLite
uses `test-results/cipher-vault.sqlite3` by default; set `CIPHER_VAULT_DB_PATH` to
choose another local database file. M4 adds the browser game.
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

`make test` runs unit and SQLite integration checks. Local JUnit and summary files
stay under ignored `test-results/`. Pull requests run lint, typing, architecture,
unit and integration checks.
