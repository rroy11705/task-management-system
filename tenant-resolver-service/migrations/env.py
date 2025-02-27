"""
Alembic environment configuration.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the parent directory to sys.path to allow imports from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the SQLAlchemy models to enable Alembic to detect model changes
from database import Base
from models import TenantModel

# This is the Alembic Config object, which provides access to the values within the .ini file
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Set the target metadata for 'autogenerate' support
target_metadata = Base.metadata

# Other values from the config, defined by the needs of env.py,
# can be acquired:
# ... etc.

def get_url():
    """Get database URL from environment variable or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@tenant-db:5432/tenant_resolver"
    )

def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a connection with the context.
    """
    # Override the URL in the alembic.ini file with our environment variable
    alembic_config = config.get_section(config.config_ini_section)
    alembic_config['sqlalchemy.url'] = get_url()
    
    # Create an engine using the configuration
    connectable = engine_from_config(
        alembic_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Prevents Alembic from creating a single transaction for all migrations
            # This is necessary when the migrations create extensions or create databases
            transaction_per_migration=True
        )

        with context.begin_transaction():
            context.run_migrations()

# Determine whether to run migrations in online or offline mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()