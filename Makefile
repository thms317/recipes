.PHONY: install setup clean test tree docs recipe_db test-recipe-plugin install-recipe-plugin serve-docs dev-recipe-plugin lint

.DEFAULT_GOAL := setup

SHELL := /bin/bash

PROFILE_NAME := "DEFAULT"

install:
	@echo "Verifying if Homebrew is installed..."; \
	which brew > /dev/null || (echo "Homebrew is not installed. Installing Homebrew..." && /bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"); \
	echo "Installing tools..."; \
	for tool in git uv; do \
		if ! command -v $$tool >/dev/null 2>&1; then \
			echo "Installing $$tool..."; \
			brew install $$tool; \
		else \
			echo "$$tool is already installed. Skipping."; \
		fi; \
	done; \
	echo "Setting up Python..."; \
	uv python install || true; \
	echo "All tools installed successfully."

setup:
	@echo "Installing tools..."
	@{ \
		output=$$($(MAKE) install 2>&1); \
		exit_code=$$?; \
		if [ $$exit_code -ne 0 ]; then \
			echo "$$output"; \
			exit $$exit_code; \
		fi; \
	}
	@echo "All tools installed successfully."

	@echo "Setting up the project..."
	@uv sync;

	@if [ ! -d ".git" ]; then \
		echo "Setting up git..."; \
		git init -b main > /dev/null; \
	fi

	@echo "Setting up pre-commit..."
	@. .venv/bin/activate
	@.venv/bin/pre-commit install --hook-type pre-commit --hook-type commit-msg

	@echo "Setup completed successfully!"

clean:
	@echo "Uninstalling local packages..."
	@rm -rf uv.lock
	@uv sync

	@echo -e "Cleaning up project artifacts..."
	@find . \( \
		-name ".pytest_cache" -o \
		-name ".mypy_cache" -o \
		-name ".ruff_cache" -o \
		-name "dist" -o \
		-name "__pycache__" -o \
		-name ".ipynb_checkpoints" \) \
		-type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".coverage" -type f -delete 2>/dev/null || true

	@echo "Cleanup completed."
	@reset

test:
	@echo "Running tests..."
	@. .venv/bin/activate
	@uv build
	@uv sync
	@uv run pytest -v tests --cov=src --cov-report=term

tree:
	@echo "Generating project tree..."
	@tree -I '.venv|__pycache__|archive|scratch|.databricks|.ruff_cache|.mypy_cache|.pytest_cache|.git|htmlcov|site|dist|.DS_Store|fixtures' -a

recipe_db:
	@echo "Generating recipe database from markdown files..."
	@. .venv/bin/activate
	@if [ ! -f "docs/database/recipes.db" ]; then \
		echo "Creating new recipe database..."; \
		uv run python -c "import sqlite3; conn = sqlite3.connect('docs/database/recipes.db'); conn.close()"; \
	fi
	@echo "Parsing recipe markdown files and populating database..."
	@PYTHONPATH=$(CURDIR) uv run python -c "from src.recipes import populate_database; populate_database()"

docs: recipe_db
	@echo "Serving recipes..."
	@. .venv/bin/activate
	@PYTHONPATH=$(CURDIR) uv run mkdocs serve

test-recipe-plugin:
	@echo "Running recipe plugin tests..."
	@. .venv/bin/activate
	@uv run pytest tests/test_recipe_plugin.py -v

install-recipe-plugin:
	@echo "Installing recipe plugin with uv..."
	@. .venv/bin/activate
	@uv pip install -e .

serve-docs: install-recipe-plugin
	@echo "Serving documentation with MkDocs..."
	@. .venv/bin/activate
	@PYTHONPATH=$(CURDIR) uv run mkdocs serve

dev-recipe-plugin: clean install-recipe-plugin test-recipe-plugin serve-docs

lint:
	@echo "Linting the project..."
	@uv sync
	@uv build
	@echo "Running ruff..."
	@uv run ruff check --output-format=concise .
	@echo "Running mypy..."
	@uv run mypy .
	@echo "Running pydoclint..."
	@uv run pydoclint .
	@echo "Running bandit..."
	@uv run bandit --configfile=pyproject.toml --severity-level=medium -r .
	@echo "Linting completed successfully!"
