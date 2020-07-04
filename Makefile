.PHONY: clean config develop docker-build docker-clean docker-clean-full docker-server docker-test-build docker-test-clean docker-test init test
DOCKER_TAG?=latest

config:
	cp develop.env.example develop.env

docker-build:
	docker-compose build

docker-clean:
	docker-compose down -v --remove-orphans

docker-clean-full: docker-clean docker-test-clean docker-minio-clean

docker-up:
	docker-compose up

docker-minio-clean:
	rm -rf tmp/docker

docker-release:
	docker push augerai/a2ml:${DOCKER_TAG}

docker-tag: docker-build
	docker tag augerai/a2ml:latest augerai/a2ml:${DOCKER_TAG}

docker-test-build:
	docker-compose -f docker-compose.test.yml build

docker-test-clean:
	docker-compose -f docker-compose.test.yml down -v --remove-orphans

docker-test: docker-test-clean docker-minio-clean docker-test-build
	docker-compose -f docker-compose.test.yml run --rm a2ml

build: clean
	python setup.py -q bdist_wheel sdist

clean:
	@find . -name '__pycache__' | xargs rm -rf
	@rm -rf a2ml.egg-info htmlcov build dist

develop:
	pip install -e ".[all]"

develop-docs:
	pip install -r docs/requirements.txt
	pip install .

init:
	virtualenv .venv

install: build
	pip install -U dist/*

release: build
	@pip install -q twine
	twine check dist/*
	twine upload dist/*

test:
	python -m py.test tests
