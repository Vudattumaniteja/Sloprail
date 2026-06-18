.PHONY: setup test lint check clean

setup:
	python -m pip --version

test:
	python -m unittest discover -s tests

lint:
	python scripts/validate_project.py

check: test lint

clean:
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist __pycache__ rmdir /s /q __pycache__
