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
