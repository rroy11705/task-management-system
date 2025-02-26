# 🏗 Tenant Management System

A **multi-tenant subdomain resolver service** using **FastAPI + PostgreSQL**, responsible for dynamically mapping subdomains to **tenant-specific database URLs**.

---

## 🚀 Features
- **Subdomain-Based Tenant Resolution** (`tenant1.example.com` → `tenant1_user_db`, `tenant1_order_db`)
- **FastAPI Middleware for Dynamic DB Switching**
- **PostgreSQL for Tenant Database Storage**
- **Alembic for Database Migrations**
- **Scalable Multi-Tenant Architecture**

## 📁 Project Structure
```bash
├── tenant_resolver/
│   ├── database.py          # PostgreSQL connection
│   ├── models.py            # Tenant model
│   ├── tenant_resolver.py   # Resolves tenant DBs
│   ├── seed_tenants.py      # Seed sample tenants
│   ├── middleware.py        # Extracts tenant info from request
│   ├── main.py              # API for tenant resolution
│   ├── requirements.txt     # Dependencies
│   ├── README.md            # Documentation
│   ├── migrations/          # Alembic migrations
│   ├── .env                 # Environment variables
│
```

---

## 📌 Requirements
- **Python 3.8+**
- **PostgreSQL**
- **FastAPI**
- **Uvicorn**
- **SQLAlchemy**
- **Alembic**
- **Docker (optional)**

---

## 📦 Installation
### 1️⃣ Clone the Repository
```sh
git clone https://github.com/your-repo/tenant-resolver.git
cd tenant-resolver
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
### 3️⃣ Set Up PostgreSQL
Run PostgreSQL manually or via Docker:

```sh
docker run --name tenant_db -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin -e POSTGRES_DB=tenant_db -p 5434:5434 -d postgres
```
we are using port 5434 for running postgres in the container

### 4️⃣ Configure Environment Variables
📌 Create .env in tenant-resolver/

```ini
DATABASE_URL=postgresql://admin:admin@localhost/tenant_db
```
