## Thesis Backend

This folder defines the backend (python) API for this project.

### Setup

````bash
pip install virtualenv
virtualenv .venv
. .venv/bin/activate

# install poetry project (defined by pyproject.toml)
pip install poetry
poetry install
````

### Usage

Start dev server, then vist http://localhost:8000

* You can also visit http://localhost:8000/docs (swagger docs)
* And view OpenAPI schema at http://localhost:8000/openapi.json

````bash
# ensure DB is up to date
./manageDB.py --maybe-migrate

# start dev server
./launch_dev.py

# upon updating database models, be sure to create an alembic revision
alembic revision --autogenerate -m "some description"
````

### Best Practices

When defining models, see these notes on [SqlAlchemy 2.0](https://docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html#orm-declarative-models) (particularly on the use of `Mapped` and `mapped_column`).