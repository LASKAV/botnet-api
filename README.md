# botnet-api

## How to deal with database

### Run migrations to the latest version

```bash
alembic upgrade head
```

### View migration SQL code (offline mode)

```bash
alembic upgrade head --sql
```

### Generate new migration

```bash
alembic revision --autogenerate -m "message"
```

**Be sure to check if the correct operations have been generated!**
