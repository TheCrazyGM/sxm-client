.PHONY: all check clean clean-build clean-pyc dev-setup format format-html git imports lint quality test
# Set the default goal so that running `make` without arguments executes code quality tasks
.DEFAULT_GOAL := quality

# -----------------------------------------------------------------------------
# Unified code quality target
# -----------------------------------------------------------------------------
all: quality

test:
	@echo "Test suite not implemented yet."

quality:
	@echo "Running import sorting (ruff --select I)"
	$(MAKE) imports
	@echo "Running code formatter (ruff format)"
	$(MAKE) format
	@echo "Running Python linter (ruff check)"
	$(MAKE) lint
	@echo "Running HTML/Jinja formatter (djhtml)"
	$(MAKE) format-html
	@echo "All code quality checks complete."

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info
	rm -fr __pycache__/ .eggs/ .cache/ .tox/

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

lint:
	uv run ruff check --fix app

format-html:
	uvx djhtml app/templates

imports:
	uv run ruff check --select I --fix app

format:
	uv run ruff format app

git:
	git push --all
	git push --tags

check:
	uv pip check

dev-setup:
	uv sync --dev
