
.PHONY: clean config develop docker-build docker-clean docker-clean-full docker-server docker-test-build docker-test-clean docker-test init test

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

docker-test-build:
	docker-compose -f docker-compose.test.yml build

docker-test-clean:
	docker-compose -f docker-compose.test.yml down -v --remove-orphans

docker-test: docker-test-clean docker-minio-clean docker-test-build
	docker-compose -f docker-compose.test.yml run --rm tests

build: clean
	python setup.py -q bdist_wheel sdist

clean:
	@find . -name '__pycache__' | xargs rm -rf
	@rm -rf "*.egg-info" htmlcov build dist

develop:
	pip install -e ".[all]"

init:
	virtualenv .venv

release: build
	@pip install -q twine
	twine check dist/*
	twine upload dist/*

test:
	python -m py.test tests
