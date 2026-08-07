.PHONY: setup test lint sync

setup:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/

coverage:
	coverage run -m pytest && coverage lcov

lint:
	pre-commit run --all-files

sync:
	python setup.py build_py
