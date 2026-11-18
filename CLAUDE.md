# Cipher Vault contribution rules

- Python 3.14, uv, FastAPI and Pydantic. No dependency major-version caps.
- M1 establishes terminology, package boundaries and verification only.
- Domain rules use the Python standard library; they never import web or storage code.
- Application coordinates domain objects and ports; infrastructure implements ports.
- Presentation translates HTTP data; composition wires adapters from the package root.
- Run `make check` locally. Keep generated results, SQLite databases and credentials untracked.
- Use one issue and one small pull request per purpose. Do not add generated author signatures.
- CI runs lint, typing, architecture and unit checks on pull requests only.
- No containers, external artwork, external model services or deployment in this milestone.
- Keep `docs/theory` in step with the code: a new rule gets a page section, a figure and a table
  row in the same pull request; `make theory-figs` and `make theory-check` must pass, and the
  README's statement count (8) must match the table.
- Style: `make fmt` rewrites, `make check-style` = `make lint` (Ruff format check + every Ruff rule) and
  `make typecheck` (mypy strict). No ignore files, excludes or inline suppressions; fix the code. The only
  rules left out are the pairs Ruff marks incompatible (D203/D213, COM812) and S101 in tests (pytest asserts).
