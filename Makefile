install:
	pip install -r requirements.txt

test:
	pytest

unit:
	pytest tests/unit -v

integration:
	pytest tests/integration -v

ci:
	ruff check src tests
	ruff format --check src tests
	pytest tests/unit -v

docker-check:
	docker build -t financial-platform:test .

lint:
	ruff check src tests

format:
	ruff format src tests

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f api
