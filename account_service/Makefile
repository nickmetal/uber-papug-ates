SHELL := /bin/bash
.PHONY: clean clean-test clean-pyc clean-build docs help


clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache


build-docker:
	docker build -f Dockerfile.rabbit -t rabbit_streams .

run-docker:
	docker run -d --rm --hostname my-rabbit -p 15672:15672 -p 5671:5671 -p 5672:5672 --name rabbit_streams_c rabbit_streams


run-migrations:
	python manage.py makemigrations account && python manage.py migrate

run-dev-server:
	python manage.py runserver 0.0.0.0:8888
