.PHONY: clean clean-test clean-build clean-pyc test lint format help install dev
.DEFAULT_GOAL := help

help:
	@echo "Commands:"
	@echo "  clean      remove all build, test, and Python artifacts"
	@echo "  clean-pyc  remove Python file artifacts"
	@echo "  clean-test remove test artifacts"
	@echo "  clean-build remove build artifacts"
	@echo "  lint       check style with flake8"
	@echo "  test       run tests quickly with pytest"
	@echo "  format     format code with isort and black"
	@echo "  install    install the package"
	@echo "  dev        install development dependencies"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint:
	flake8 src tests

test:
	pytest

format:
	isort src tests
	black src tests

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pip install -r requirements-dev.txt 