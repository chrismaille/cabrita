install:
	@poetry install
	@poetry run pre-commit install -f

update:
	@poetry update
	@poetry run pre-commit autoupdate

test:
	@poetry run pytest -v -x -p no:warnings --cov-report term-missing --cov=./cabrita

ci:
	@poetry run pytest --cov=./cabrita --black --flake8

format:
	@poetry run black .
