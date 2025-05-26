import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# —————————————————————————————————————————————————————————————————————————————
# 1) Make sure your app’s root is on PYTHONPATH:
#    (so that `import core.database` and `import models.user` work)
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# 2) Load Pydantic settings (which assembles your .env URL)
from core.config import settings

# 3) Override the sqlalchemy.url in alembic.ini with your Settings value
config = context.config
config.set_main_option(
    "sqlalchemy.url",
    str(settings.SQLALCHEMY_DATABASE_URI)
)

# 4) Import your Base and *all* of your model modules so they register on Base.metadata
from core.database import Base           # <— your declarative_base()
import models.user                       # each import defines one or more tables
import models.role
import models.privilege
import models.sample
import models.oauth_account
import models.admin_logging_setting # Added for the new model
# …if you have any other files under `models/`, import them here as well

# 5) Tell Alembic about your metadata
target_metadata = Base.metadata
# —————————————————————————————————————————————————————————————————————————————

# keep the rest of the file as Alembic generated:
fileConfig(config.config_file_name)
# … run_migrations_offline, run_migrations_online, etc.
# … everything up through target_metadata = Base.metadata …

from alembic import context

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (using a DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # these flags help Alembic pick up changes in column types/defaults
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
