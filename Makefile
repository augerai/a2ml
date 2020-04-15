
.PHONY: build clean init server test-build test

build:
	docker-compose build

clean:
	docker-compose down -v --remove-orphans

init:
	cp develop.env.example develop.env

server:
	docker-compose up

test-build:
	docker-compose -f docker-compose.test.yml build

test:
	docker-compose -f docker-compose.test.yml run tests
