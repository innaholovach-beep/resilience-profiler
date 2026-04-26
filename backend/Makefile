install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	python -m pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	flake8 app/ tests/