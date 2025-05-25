# Docs

## scaffold a brand-new initial migration

alembic revision --autogenerate -m "Initial create all tables"

## apply the migration to the database

alembic upgrade head
