After creating a model, to create migrations files: ` python -m alembic revision --autogenerate -m "create table"`
After taht to migrate into DB: `python -m alembic upgrade head`
