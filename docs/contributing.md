# Contributor development notes

The canonical contribution guide is [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## Local checks

```bash
python -m pip install -e ".[dev]"
ruff check src tests
pytest
```

Tests should not require a running Ollama instance unless explicitly marked as
integration tests. Never use confidential documents as fixtures.
