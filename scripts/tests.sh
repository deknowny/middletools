source .env
poetry run tox -q
poetry run coveralls