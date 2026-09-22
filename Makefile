install:
	pip install -r requirements.txt

test:
	pytest

unit:
	pytest tests/unit -v

security:
	pytest tests/security -v

integration:
	pytest -m integration -v

eval:
	python evals/experiments/run_full_eval.py

rag-crag-eval:
	python evals/experiments/compare_rag_crag.py

risk-eval:
	python evals/experiments/run_risk_eval.py

llm-eval:
	pytest -m llm -v

e2e:
	pytest -m e2e -v

quality:
	ruff check src tests
	ruff format --check src tests
	pytest tests/unit -v
	pytest tests/security -v

ci: quality

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

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(m)"

migration-current:
	alembic current

migration-history:
	alembic history
