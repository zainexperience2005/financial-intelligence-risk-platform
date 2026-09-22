# Database Migrations

The application uses Alembic for schema migrations.

Normal application startup must not create or modify
database schemas.

## New environment

Run:

    alembic upgrade head

before starting the application.

## Existing pre-Alembic database

Verify that the existing schema matches the reviewed
baseline migration before running:

    alembic stamp head

Stamping records migration state and does not execute
schema changes.

## Schema changes

1. Modify SQLAlchemy models.
2. Generate an Alembic revision.
3. Review upgrade and downgrade operations.
4. Test against disposable PostgreSQL.
5. Run integration tests.
6. Commit the model and migration together.

Model-generated SQL continues to use the read-only
database role and never receives migration privileges.

## Makefile shortcuts

- `make migrate`: Apply all pending migrations (`alembic upgrade head`).
- `make migration m="description"`: Autogenerate a new migration script.
- `make migration-current`: Inspect current database migration revision.
- `make migration-history`: View historical revisions.
