.PHONY: setup test lint sync

setup:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/

lint:
	pre-commit run --all-files

sync:
	python setup.py build_py
