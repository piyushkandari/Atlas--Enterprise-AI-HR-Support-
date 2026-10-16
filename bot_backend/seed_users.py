"""Create demo users. Run: python -m bot_backend.seed_users"""
from .database import Base, engine, SessionLocal
from .models import User
from .security import hash_password

DEMO = [
    # (email, password, emp_code, role)
    ("bob@company.com",   "password123", "E002", "employee"),
    ("alice@company.com", "password123", "E001", "employee"),
    ("david@company.com", "password123", "E004", "hr"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created = 0
        for email, pwd, emp_code, role in DEMO:
            if db.query(User).filter_by(email=email).first():
                continue
            db.add(User(email=email, password_hash=hash_password(pwd),
                        emp_code=emp_code, role=role))
            created += 1
        db.commit()
        print(f"Seeded users. Created {created} new (skipped existing).")
    finally:
        db.close()


if __name__ == "__main__":
    main()