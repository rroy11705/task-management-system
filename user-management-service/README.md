# User Management Service

A comprehensive authentication and authorization service that manages users, roles, and permissions for the Task Management System microservices architecture.

## Overview

The User Management Service provides centralized user authentication, JWT token generation, role-based access control (RBAC), and permission management. It's a core component in the Task Management System's microservices architecture, ensuring proper access control across all services.

## Key Features

- **User Authentication**: Secure email/username and password-based authentication with JWT tokens
- **User Management**: Create, update, deactivate, and reactivate user accounts
- **Role-Based Access Control**: Flexible RBAC system with predefined and custom roles
- **Permission Management**: Fine-grained permission system for precise access control
- **Multi-Tenant Support**: Segregation of users by tenant with tenant-specific permissions
- **Event Publishing**: Broadcasts user events to other services via RabbitMQ
- **RESTful API**: Clean interface for all user management operations

## Technical Architecture

The User Management Service is built with:

- **FastAPI**: Modern, high-performance web framework
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **Alembic**: Database migration tool
- **PostgreSQL**: Robust relational database
- **JWT (JSON Web Tokens)**: For secure, stateless authentication
- **Passlib + Bcrypt**: For secure password hashing
- **RabbitMQ**: Message broker for event-driven communication

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with username/email and password, returns JWT token |
| POST | `/auth/register` | Register a new user |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get current authenticated user details |
| GET | `/users/{user_id}` | Get user details by ID |
| GET | `/users` | Get all users (optionally filtered by tenant) |
| PUT | `/users/{user_id}` | Update user details |
| PUT | `/users/{user_id}/deactivate` | Deactivate a user |
| PUT | `/users/{user_id}/reactivate` | Reactivate a user |

### Role Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/roles` | Get all roles |
| POST | `/roles` | Create a new role |
| GET | `/users/{user_id}/roles` | Get roles for a user |
| POST | `/users/{user_id}/roles` | Assign a role to a user |
| DELETE | `/users/{user_id}/roles/{role_id}` | Remove a role from a user |
| GET | `/roles/{role_id}/permissions` | Get permissions for a role |

### Permission Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/permissions` | Get all permissions |
| POST | `/permissions` | Create a new permission |
| POST | `/roles/{role_id}/permissions` | Assign a permission to a role |
| DELETE | `/roles/{role_id}/permissions/{permission_id}` | Remove a permission from a role |

## Default Roles and Permissions

The service automatically bootstraps these roles on startup:

**Roles:**
- **Admin**: Full system access
- **Manager**: Project and task management, analytics viewing
- **Member**: Basic project and task operations
- **Viewer**: Read-only access

**Permission Categories:**
- Project operations: create, update, delete projects
- Task operations: create, update, delete, assign tasks
- User management: manage users, assign roles
- Analytics: view analytics data

## Authentication Flow

1. User logs in with email/username and password
2. Service verifies credentials and generates a JWT token
3. Token includes user ID, tenant ID, and expiration
4. Client includes token in Authorization header for subsequent requests
5. Service validates token and enforces permissions

## RBAC (Role-Based Access Control)

The service implements a flexible RBAC system where:
- Users are assigned to one or more roles
- Roles contain one or more permissions
- Permissions represent specific actions a user can perform
- Endpoints can be protected with specific permission requirements

## Event Publishing

The service publishes these events to other microservices:
- UserCreated
- UserUpdated 
- UserPermissionChanged
- UserDeactivated/Reactivated

## Setup and Installation

### Prerequisites

- Python 3.9+
- PostgreSQL
- RabbitMQ
- Docker (optional)

### Environment Variables

Set these environment variables or create a `.env` file:

```
DATABASE_URL=postgresql://username:password@host:port/user_management
JWT_SECRET=your_jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd user-management-service
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the service:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8002 --reload
   ```

### Running with Docker

```bash
docker build -t user-management-service .
docker run -p 8002:8002 -d --env-file .env user-management-service
```

Or using docker-compose:

```bash
docker-compose up -d user-management
```

## API Usage Examples

### User Registration

```bash
curl -X POST "http://localhost:8002/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
           "email": "user@example.com",
           "username": "username",
           "password": "SecurePass123!",
           "first_name": "John",
           "last_name": "Doe",
           "tenant_id": "tenant1"
         }'
```

### User Login

```bash
curl -X POST "http://localhost:8002/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=username&password=SecurePass123!"
```

### Assigning a Role to a User

```bash
curl -X POST "http://localhost:8002/users/{user_id}/roles" \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{"role_id": "{role_id}"}'
```

## Integration with Other Services

This service integrates with other microservices in the Task Management System:

- **API Gateway**: Validates JWT tokens from User Management Service
- **Tenant Resolver Service**: Coordinates tenant databases
- **Project Service**: Uses user permissions from User Management Service
- **Analytics Service**: Processes user events for analytics
- **URL Shortener Service**: Uses user information for tracking URL creators

## Contributing

Guidelines for contributing to the project will be added here.

## License

This project is licensed under the MIT License - see the LICENSE file for details.