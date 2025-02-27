"""
Service for managing tenant databases.
"""

import os
import psycopg2
import subprocess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import TenantModel

def get_admin_connection():
    """
    Get a connection to the PostgreSQL server with admin privileges.
    """
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5434")
    
    conn = psycopg2.connect(
        dbname="postgres",
        user=admin_user,
        password=admin_password,
        host=host,
        port=port
    )
    conn.autocommit = True
    return conn

def provision_database(tenant: TenantModel):
    """
    Provision a new database for a tenant.
    """
    conn = get_admin_connection()
    cursor = conn.cursor()
    
    try:
        # Create a new database for the tenant
        cursor.execute(f"CREATE DATABASE {tenant.db_name}")
        
        # Create a database user with limited permissions
        cursor.execute(f"CREATE USER {tenant.db_user} WITH PASSWORD '{tenant.db_password}'")
        
        # Grant permissions to the user
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {tenant.db_name} TO {tenant.db_user}")
        
        print(f"Database {tenant.db_name} and user {tenant.db_user} created successfully")
    except Exception as e:
        print(f"Error provisioning database: {str(e)}")
        # Clean up any partially created resources
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {tenant.db_name}")
            cursor.execute(f"DROP USER IF EXISTS {tenant.db_user}")
        except:
            pass
        raise
    finally:
        cursor.close()
        conn.close()

def get_tenant_db_engine(tenant: TenantModel):
    """
    Get a SQLAlchemy engine for a tenant database.
    """
    db_url = f"postgresql://{tenant.db_user}:{tenant.db_password}@{tenant.db_host}:{tenant.db_port}/{tenant.db_name}"
    return create_engine(db_url)

def run_migrations(tenant: TenantModel):
    """
    Run database migrations for a tenant.
    """
    print(f"Running migrations for tenant {tenant.name} (ID: {tenant.id})")
    
    # In a production environment, you'd use alembic programmatically
    # But for simplicity, we're using subprocess to run alembic commands
    
    # Get the path to the migrations directory
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")
    
    # Set environment variables for alembic
    env = os.environ.copy()
    env["TENANT_DB_URL"] = f"postgresql://{tenant.db_user}:{tenant.db_password}@{tenant.db_host}:{tenant.db_port}/{tenant.db_name}"
    
    try:
        # Run alembic migrations
        subprocess.run(
            ["alembic", "upgrade", "head"], 
            cwd=migrations_dir,
            env=env,
            check=True
        )
        print(f"Migrations for tenant {tenant.id} completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {str(e)}")
        raise Exception(f"Failed to run migrations: {str(e)}")