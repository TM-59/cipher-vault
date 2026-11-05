# M1 requirements and verification

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
applicable to this milestone's health-only scaffold. Domain tests arrive in M2,
SQLite integration in M3 and browser smoke in M4. These omissions are not passes.

## References

- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Starlette TestClient and httpx2](https://starlette.dev/testclient/)
- [Import Linter layers](https://import-linter.readthedocs.io/en/stable/contract_types/layers/)
- [uv locked environments](https://docs.astral.sh/uv/concepts/projects/sync/)

References checked 2026-11-06. Vocabulary was drafted locally and reviewed against
the explicit game constraints; the final definitions and examples were checked by hand.
