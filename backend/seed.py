"""Seed the database with initial users."""
import asyncio
import sys

sys.path.insert(0, ".")

from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import hash_password


async def seed():
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.email == "admin@thaiestate.com"))
        if result.scalar_one_or_none():
            print("Admin already exists. Skipping seed.")
            return

        users = [
            User(
                name="Super Admin",
                email="admin@thaiestate.com",
                password_hash=hash_password("admin123"),
                role="Admin",
                status="active",
            ),
            User(
                name="Manager Demo",
                email="manager@thaiestate.com",
                password_hash=hash_password("manager123"),
                role="Manager",
                status="active",
            ),
            User(
                name="Agent Demo",
                email="agent@thaiestate.com",
                password_hash=hash_password("agent123"),
                role="Agent",
                status="active",
            ),
            User(
                name="Viewer Demo",
                email="viewer@thaiestate.com",
                password_hash=hash_password("viewer123"),
                role="Viewer",
                status="active",
            ),
        ]

        for u in users:
            db.add(u)
        await db.commit()
        print(f"Seeded {len(users)} users:")
        for u in users:
            print(f"  {u.role:8s} | {u.email:30s} | password: {u.role.lower()}123")


if __name__ == "__main__":
    asyncio.run(seed())
