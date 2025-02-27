# 🏗️ Tenant Resolver Service

A **multi-tenant subdomain resolver service** using **FastAPI + PostgreSQL**, responsible for dynamically mapping subdomains to **tenant-specific database URLs** within the Task Management System microservices architecture.

## 🚀 Features

- **Subdomain-Based Tenant Resolution**: Maps `tenant1.example.com` to appropriate tenant-specific database connections
- **Dynamic Database Provisioning**: Automatically creates dedicated PostgreSQL databases for new tenants
- **Secure Database Credential Management**: Generates and securely stores unique credentials for each tenant
- **Database Migration Management**: Coordinates Alembic migrations across tenant databases
- **Event Publishing**: Notifies other services about tenant lifecycle events via RabbitMQ
- **RESTful API**: Clean interface for tenant and database operations

## 🔧 Technical Architecture

The Tenant Resolver Service is built with:

- **FastAPI**: Modern, high-performance web framework
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **Alembic**: Database migration tool
- **PostgreSQL**: Robust relational database
- **RabbitMQ**: Message broker for event-driven communication

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check endpoint |
| POST | `/tenants` | Create a new tenant and provision its database |
| GET | `/tenants/{tenant_id}` | Get tenant details by ID |
| GET | `/tenants/by-subdomain/{subdomain}` | Get tenant details by subdomain |
| GET | `/tenants/{tenant_id}/database` | Get database connection details for a tenant |
| POST | `/tenants/{tenant_id}/migrations` | Run database migrations for a tenant |

## 🔄 Database Schema

The service maintains tenant information in the following schema:

```
tenants
├── id (PK)
├── name
├── subdomain (unique)
├── db_name
├── db_host
├── db_port
├── db_user
├── db_password
├── is_active
├── created_at
└── updated_at
```

## 📦 Installation

### Prerequisites

- **Python 3.9+**
- **PostgreSQL**
- **RabbitMQ**
- **Docker** (optional)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tenant-resolver-service
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with the following variables:
   ```
   DATABASE_URL=postgresql://admin:admin@localhost:5432/tenant_resolver
   RABBITMQ_URL=amqp://guest:guest@localhost:5672/
   POSTGRES_ADMIN_USER=postgres
   POSTGRES_ADMIN_PASSWORD=postgres
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

4. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

5. **Run the service**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

## 🐳 Docker Deployment

You can also run the service using Docker:

```bash
docker build -t tenant-resolver-service .
docker run -p 8001:8001 --env-file .env tenant-resolver-service
```

Or using docker-compose:

```bash
docker-compose up -d tenant-resolver
```

## 🔍 Usage Examples

### Creating a New Tenant

```bash
curl -X POST "http://localhost:8001/tenants" \
     -H "Content-Type: application/json" \
     -d '{"name": "Example Organization", "subdomain": "example"}'
```

### Retrieving Tenant Database Connection

```bash
curl -X GET "http://localhost:8001/tenants/by-subdomain/example" 
curl -X GET "http://localhost:8001/tenants/{tenant_id}/database"
```

## 🤝 Integration with Other Services

This service is designed to work with the other microservices in the Task Management System:

- **API Gateway**: Routes requests based on subdomain
- **Project Service**: Uses tenant database connections for data storage
- **User Management Service**: Associates users with tenants
- **Analytics Service**: Uses tenant information for data aggregation

## 📃 License

This project is licensed under [MIT License] - see the LICENSE file for details.