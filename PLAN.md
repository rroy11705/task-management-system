# Task Management System - Microservices Architecture Masterplan

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Microservices Breakdown](#microservices-breakdown)
4. [Data Architecture](#data-architecture)
5. [Event-Driven Communication](#event-driven-communication)
6. [Security & Authentication](#security--authentication)
7. [Development Roadmap](#development-roadmap)
8. [Technical Considerations](#technical-considerations)
9. [Future Expansion](#future-expansion)

## Project Overview

### Objectives
- Create a task management system with Kanban board functionality
- Implement a microservices architecture using FastAPI and Docker
- Support multi-tenant isolation with separate databases per tenant
- Enable task sharing via URL shortening with expiration and password protection
- Provide analytics for task management and URL usage
- Learn and implement best practices for microservices development

### Target Audience
- Organizations requiring task management across teams
- Managers who need to track project progress
- Teams collaborating on various projects with different access requirements
- Administrators requiring analytics for oversight and reporting

## System Architecture

### High-Level Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│   API Gateway   │─────▶│ Tenant Resolver │─────▶│    User Mgmt    │
│    (FastAPI)    │      │    Service      │      │    Service      │
│                 │      │                 │      │                 │
└────────┬────────┘      └─────────────────┘      └─────────────────┘
         │
         │
         ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│ Project Service │◀────▶│  URL Shortener  │◀────▶│   Analytics     │
│  (per-tenant)   │      │    Service      │      │    Service      │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘

            ▲                   ▲                   ▲
            │                   │                   │
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │
                        ┌───────────────┐
                        │               │
                        │   RabbitMQ    │
                        │               │
                        └───────────────┘
```

### Containerization Strategy
- Each microservice deployed as an independent Docker container
- Docker Compose for local development orchestration
- PostgreSQL containers for relational data (tenant-specific)
- MongoDB container for analytics data
- RabbitMQ container for event-driven communication

## Microservices Breakdown

### 1. API Gateway Service
**Purpose**: Acts as the entry point for all client requests, routing them to appropriate microservices.

**Key Responsibilities**:
- Route API requests to appropriate backend services
- Extract and validate JWT tokens
- Extract tenant information from subdomain
- Implement basic rate limiting
- Handle cross-cutting concerns like logging and error handling

**Technology Stack**:
- FastAPI framework
- No database required

### 2. Tenant Resolver Service
**Purpose**: Manages organization subdomains and their corresponding database connections.

**Key Responsibilities**:
- Map subdomains to tenant IDs
- Dynamically create databases for new tenants
- Manage database connection details for each tenant
- Coordinate database migrations across tenant databases

**Technology Stack**:
- FastAPI framework
- PostgreSQL for tenant mapping storage

### 3. Centralized User Management Service
**Purpose**: Handles authentication, authorization, and user management across the system.

**Key Responsibilities**:
- User registration and authentication
- JWT token generation and validation
- Role-based access control
- Organization user management
- Permission assignment

**Technology Stack**:
- FastAPI framework
- PostgreSQL for user data storage
- JWT for token-based authentication

### 4. Project Service
**Purpose**: Manages projects, tasks, and Kanban boards.

**Key Responsibilities**:
- Project CRUD operations
- Kanban board management
- Task and subtask management
- Comments and attachments
- Work logs and time tracking

**Technology Stack**:
- FastAPI framework
- PostgreSQL databases (per-tenant)
- SQLAlchemy ORM with Alembic migrations

### 5. URL Shortener Service
**Purpose**: Creates and manages shortened URLs for sharing tasks.

**Key Responsibilities**:
- Generate shortened URLs using hash-based approach
- Manage URL expiration dates
- Implement password protection for URLs
- Track URL usage for analytics
- Handle URL redirections

**Technology Stack**:
- FastAPI framework
- Dedicated PostgreSQL database
- Cryptographic libraries for secure hashing

### 6. Analytics Service
**Purpose**: Collects and processes analytics data for tasks and URL usage.

**Key Responsibilities**:
- Collect URL access metrics
- Track task status changes
- Generate dashboard data for administrators
- Process analytics events from other services

**Technology Stack**:
- FastAPI framework
- MongoDB for analytics data storage
- Basic real-time counting with batch processing for aggregation

## Data Architecture

### Multi-Tenant Database Strategy
- Database-per-tenant model for Project Service
- Each tenant gets an isolated PostgreSQL database
- Naming convention: `tenant_{tenant_id}`
- Dynamic database creation upon tenant registration

### Shared Databases
- Tenant Resolver Service: Single PostgreSQL database for tenant mapping
- User Management Service: Single PostgreSQL database for all users
- URL Shortener Service: Dedicated PostgreSQL database for URL mappings
- Analytics Service: MongoDB database for analytics data

### Data Migration Strategy
- SQLAlchemy with Alembic for relational database migrations
- Centralized Migration Service to manage migrations across tenant databases
- Version tracking for each tenant database
- Automated migration scripts as part of deployment process

## Event-Driven Communication

### Message Broker
- RabbitMQ for asynchronous communication between services
- Dockerized deployment for local development

### Event Types
1. **User Events**:
   - UserCreated
   - UserUpdated
   - UserPermissionChanged

2. **Project Events**:
   - ProjectCreated
   - ProjectUpdated
   - ProjectUserAdded

3. **Task Events**:
   - TaskCreated
   - TaskStatusChanged
   - TaskAssigned
   - TaskCommentAdded

4. **URL Events**:
   - URLCreated
   - URLAccessed
   - URLExpired

### Event Flow Examples
- When a new task is created in the Project Service, it publishes a TaskCreated event
- The Analytics Service subscribes to TaskCreated events to track task creation metrics
- When a shortened URL is accessed, the URL Shortener Service publishes a URLAccessed event
- The Analytics Service subscribes to URLAccessed events to track URL usage

## Security & Authentication

### Authentication Flow
1. User logs in through the API Gateway
2. Request is forwarded to User Management Service
3. If credentials are valid, User Management Service generates a JWT token
4. JWT token includes user ID, tenant ID, roles, and permissions
5. Token is returned to client and used for subsequent requests
6. API Gateway validates token for each request before routing

### JWT Token Structure
```json
{
  "sub": "user123",
  "tenantId": "org1",
  "roles": ["admin", "manager"],
  "permissions": ["create_project", "assign_task"],
  "exp": 1645484400
}
```

### Authorization
- Role-based access control implemented in User Management Service
- Permission validation performed by individual services
- Tenant isolation enforced at database connection level

## Development Roadmap

### Week 1 Priority Plan

#### Day 1:
- Set up Docker environment with PostgreSQL
- Implement basic Tenant Resolver Service
- Create database provisioning logic

#### Day 2:
- Implement User Management Service with JWT authentication
- Create API Gateway with basic routing

#### Day 3:
- Implement Project Service with basic CRUD operations
- Set up RabbitMQ for event communication

#### Day 4:
- Implement Task Management features
- Create Kanban board functionality

#### Day 5:
- Implement URL Shortener Service (basic functionality)
- Set up event handling between services

#### Day 6:
- Implement basic Analytics Service with MongoDB
- Create simple dashboards for organization admins

#### Day 7:
- Testing and debugging
- Documentation
- Basic UI implementation if time permits

### Features Postponed for Week 2
- Advanced analytics (geographical tracking, referrer analysis)
- Password protection for shared URLs
- Complex permissions management
- Subtask management
- File attachments for tasks

## Technical Considerations

### Database Provisioning
The Tenant Resolver Service will handle dynamic database creation:
- Database creation triggered by tenant registration event
- PostgreSQL role creation with limited permissions
- Initial schema creation using Alembic migrations
- Connection details stored in tenant mapping database

### Migration Management
A Centralized Migration Service will:
- Maintain a registry of all tenant databases
- Track migration versions for each database
- Apply migrations sequentially to each database
- Handle migration failures gracefully

### API Gateway Implementation
The FastAPI-based API Gateway will:
- Use path-based routing to direct requests to appropriate services
- Implement JWT validation middleware
- Extract tenant information from subdomain
- Implement basic rate limiting using Redis (optional)

### URL Shortener Implementation
The URL Shortener Service will:
- Generate unique hash using combination of tenant ID and timestamp
- Store mapping between original URL and shortened URL
- Implement expiration date functionality
- Prepare for password protection in week 2
- Track basic access metrics

### Analytics Implementation
The Analytics Service will:
- Use MongoDB collections for different types of events
- Implement basic real-time counters for immediate metrics
- Use batch processing for aggregated metrics
- Provide API endpoints for dashboard data retrieval

## Future Expansion

### Potential Week 2 Enhancements
- Integration with external services (GitHub, Slack, etc.)
- Advanced reporting and analytics
- Email notifications for task updates
- Mobile application support
- Performance optimization
- Comprehensive test coverage

### Technical Improvements
- Implement API documentation using Swagger/OpenAPI
- Add comprehensive logging and monitoring
- Implement circuit breakers for fault tolerance
- Add caching layer for improved performance
- Implement comprehensive error handling strategy