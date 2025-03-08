# ArbitrageX Makefile

.PHONY: setup run run-api run-scanner test lint clean help

# Setup the project
setup:
	pip install -r requirements.txt

# Run all components
run:
	python run.py

# Run only the API server
run-api:
	python backend/api/server.py

# Run only the network scanner
run-scanner:
	python backend/bot/network_scanner.py

# Run tests
test:
	pytest

# Run linting
lint:
	flake8 backend
	mypy backend

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Help command
help:
	@echo "Available commands:"
	@echo "  make setup        - Install dependencies"
	@echo "  make run          - Run all components"
	@echo "  make run-api      - Run only the API server"
	@echo "  make run-scanner  - Run only the network scanner"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make clean        - Clean up temporary files"