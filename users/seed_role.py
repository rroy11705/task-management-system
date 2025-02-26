from sqlalchemy.orm import Session
from database import SessionLocal
from models import Role

db: Session = SessionLocal()

roles = [
    {"id": 1, "name": "admin", "permissions": "read_users,delete_users"},
    {"id": 2, "name": "manager", "permissions": "read_users"},
    {"id": 3, "name": "user", "permissions": ""},
]

for role in roles:
    if not db.query(Role).filter(Role.id == role["id"]).first():
        db.add(Role(**role))

db.commit()
db.close()
