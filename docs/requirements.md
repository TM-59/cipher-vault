# Requirements and verification (M1 and M2)

- REQ-HEALTH: GET /health returns status ok through the FastAPI/Pydantic adapter.
- REQ-CORE: domain and application import with third-party packages disabled.
- REQ-LAYERS: imports point inward, adapters remain independent, core excludes web libraries.
  Verified by `lint-imports`; intentionally forbidden imports must fail.

`make test` runs pytest only. `make check` adds lint, formatting, strict typing and
architecture checks. Each command has a 60-second execution budget; checks wait
when the one-minute system load exceeds 20. Execution is serial and uses no model,
external network, credentials, notifications or deployed resources.
JUnit and a summary are written to ignored `test-results/<run>/`, with the latest
summary also at `test-results/summary.json`. Failure/timeout results are retained.

Benchmarks, integration, browser, visual, infrastructure and trace tests are not
applicable before a screen and storage exist. Domain tests arrived in M2 (below),
SQLite integration in M3 and browser smoke in M4. These omissions are not passes.

## M2: the pure domain

Standard library only; see `tests/test_domain.py`.

- REQ-CODE: a code is four digits from 0 to 5, repeats allowed, an immutable value;
  text input must be four plain digits; feedback counts must be possible.
- REQ-SCORE: exact matches are counted first, then remaining digits without reuse.
  A hand-written table of 16 cases, and 36 secrets against all 1296 guesses checked
  against an independent count.
- REQ-ROUND: at most eight guesses; a correct guess wins, including the eighth; an
  incorrect eighth exhausts; terminal rounds and invalid input change nothing; the
  GuessScored event carries the round identity, turn, guess, feedback and state, never
  the secret.

## References

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Starlette TestClient and httpx2](https://starlette.dev/testclient/)
- [Import Linter layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/)
- [uv locked environments](https://docs.astral.sh/uv/concepts/projects/sync/)

References checked 2026-11-06. Vocabulary and examples were reviewed against the
explicit game constraints. No unverified model output is included.
