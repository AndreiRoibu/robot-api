# The default recipe that runs when you just type 'just'. It lists all available recipes.
default:
    @just --list

# Install virtual environment and pre-commit hooks
install:
	echo "🚀 Creating virtual environment and syncing dependencies with uv"
	uv sync --group dev
	echo "🚀 Installing project in editable mode"
	uv pip install --editable .
	if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
	echo "🚀 Installing pre-commit hooks"; \
	uv run pre-commit install; \
	else \
	echo "⚠️ Skipping hook installation because no Git repository was detected."; \
	echo "   Run 'uv run pre-commit run --all-files' manually to check your code."; \
	fi

# Create a virtual environment with uv
venv:
    echo "🚀 Creating virtual environment with uv in folder .venv"
    python3 -m venv .venv
    echo "🚀 Installing uv in the virtual environment"
    .venv/bin/pip install --upgrade uv

# Upgrading locked package versions
upgrade:
    echo "🚀 Upgrading locked package versions"
    uv lock --upgrade
    echo "🚀 Syncing dependencies with uv"
    uv sync --group dev
