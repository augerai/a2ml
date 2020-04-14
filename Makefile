
.PHONY: config docker-build docker-clean docker-server docker-test-build docker-test

config:
	cp develop.env.example develop.env

docker-build:
	docker-compose build

docker-clean:
	docker-compose down -v --remove-orphans

docker-clean-full: docker-clean
	rm -rf tmp/docker

docker-up:
	docker-compose up

docker-test-build:
	docker-compose -f docker-compose.test.yml build

docker-test: docker-clean docker-test-build
	docker-compose -f docker-compose.test.yml run tests
