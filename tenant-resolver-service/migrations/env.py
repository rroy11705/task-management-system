"""
Alembic environment configuration.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Base object from the models module
from database import Base

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Set the target for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    """
    # TODO: Implement offline migrations
    pass

def run_migrations_online():
    """
    Run migrations in 'online' mode.
    """
    # TODO: Implement online migrations
    pass

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()