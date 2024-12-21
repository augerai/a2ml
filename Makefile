.PHONY: clean config develop docker-build docker-clean docker-clean-full docker-server docker-test-build docker-test-clean docker-test init test
DOCKER_TAG?=latest
COMPOSE_DOCKER_CLI_BUILD=1
DOCKER_BUILDKIT=1

config:
	cp develop.env.example develop.env

docker-build:
	docker build \
		--target=base \
		--cache-from=base \
		--tag base .
	docker build \
		--target=builder \
		--cache-from=base \
		--cache-from=builder \
		--tag builder .
	docker build \
		--target=runtime \
		--cache-from=base \
		--cache-from=builder \
		--cache-from=augerai/a2ml:${DOCKER_TAG} \
		--tag augerai/a2ml:${DOCKER_TAG} .

docker-clean:
	docker compose down -v --remove-orphans

docker-clean-full: docker-clean docker-test-clean docker-minio-clean

docker-up:
	docker compose up

docker-minio-clean:
	rm -rf tmp/docker

docker-release:
	docker push augerai/a2ml:${DOCKER_TAG}

docker-load:
	gunzip image.tar.gz
	docker load -i image.tar | true

docker-save:
	docker save -o image.tar augerai/a2ml:${DOCKER_TAG}
	gzip image.tar

docker-tag:
	docker tag augerai/a2ml:latest augerai/a2ml:${DOCKER_TAG}

docker-test-clean: docker-minio-clean
	docker compose -f docker-compose.test.yml down -v --remove-orphans

docker-test: docker-build
	docker compose -f docker-compose.test.yml run --rm a2ml

build: clean
	python setup.py -q bdist_wheel sdist

clean:
	@find . -name '__pycache__' | xargs rm -rf
	@rm -rf a2ml.egg-info htmlcov build dist

develop:
	pip install -e ".[all]"

develop-docs:
	pip install -r docs/requirements.txt
	pip install .[docs]

init:
	virtualenv .venv

install: build
	pip install -U dist/*

release: build
	@pip install -q twine
	twine check dist/*
	twine upload dist/*

test:
	python -m pytest tests
