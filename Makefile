.PHONY: sync test check serve
sync:
	uv sync --locked --python 3.14
test:
	uv run --locked python scripts/check.py test
check:
	uv run --locked python scripts/check.py check
serve:
	PYTHONPATH=src uv run --locked uvicorn cipher_vault.composition:create_app --factory --host localhost
