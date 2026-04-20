.PHONY: help install install-dev test lint format clean run

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies using UV"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Format code with black and ruff"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make run           - Run the main task"
	@echo "  make pre-commit    - Run pre-commit hooks"

install:
	uv pip install -r requirements.txt

install-dev:
	uv pip install -r requirements.txt
	uv pip install pytest pytest-cov pytest-mock black ruff mypy pre-commit
	pre-commit install

test:
	pytest --cov=libraries --cov=Workflow --cov-report=term-missing --cov-report=html -v

lint:
	black --check --line-length=100 .
	ruff check .
	mypy . --ignore-missing-imports || true

format:
	black --line-length=100 .
	ruff check --fix .

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

run:
	python tasks.py

pre-commit:
	pre-commit run --all-files

