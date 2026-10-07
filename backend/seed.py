from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


def seed_roles(db):
    roles = [
        "ADMIN",
        "SUPPORT_AGENT",
        "CUSTOMER",
    ]

    for role_name in roles:
        existing_role = db.scalar(
            select(Role).where(Role.name == role_name)
        )

        if not existing_role:
            db.add(Role(name=role_name))

    db.commit()


def get_role(db, role_name):
    return db.scalar(
        select(Role).where(Role.name == role_name)
    )


def seed_user(
    db,
    name,
    email,
    password,
    role_name,
):
    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        print(f"{email} already exists")
        return

    role = get_role(db, role_name)

    if not role:
        print(f"Role {role_name} not found")
        return

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role_id=role.id,
        is_active=True,
    )

    db.add(user)
    db.commit()

    print(f"{email} created successfully")


def seed_admin(db):
    seed_user(
        db=db,
        name="System Admin",
        email="admin@support.com",
        password="Admin@123",
        role_name="ADMIN",
    )


def seed_support_agent(db):
    seed_user(
        db=db,
        name="Support Agent",
        email="agent@support.com",
        password="Agent@123",
        role_name="SUPPORT_AGENT",
    )


def seed_customer(db):
    seed_user(
        db=db,
        name="Test Customer",
        email="customer@test.com",
        password="Customer@123",
        role_name="CUSTOMER",
    )


def main():
    db = SessionLocal()

    try:
        seed_roles(db)

        seed_admin(db)
        seed_support_agent(db)
        seed_customer(db)

    finally:
        db.close()


if __name__ == "__main__":
    main()