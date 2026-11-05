# Cipher Vault

A codebreaking puzzle built with Python and FastAPI, one small milestone at a time.
The first milestone establishes the vocabulary and architecture; gameplay follows later.

Planned rules: find a four-digit code in eight guesses. Digits 0-5 may repeat;
feedback reports exact matches and digit-only matches. See [the domain design](docs/domain.md)
and [verification scope](docs/requirements.md).

## Run the scaffold

Install Python 3.14 and [uv](https://docs.astral.sh/uv/), then:

```sh
make sync
make check
make serve
```

`GET http://localhost:8000/health` returns `{"status":"ok"}`. The server is local.
No game screen or database exists yet; M2 introduces the pure domain, M3 adds SQLite,
and M4 adds the browser game. No screenshots are claimed before a playable screen exists.

`make test` runs the unit checks. Local JUnit and summary files stay under ignored
`test-results/`. Pull requests run lint, typing, architecture and unit checks only.
