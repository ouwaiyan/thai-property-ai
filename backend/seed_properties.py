"""Seed sample properties."""
import asyncio
import sys
sys.path.insert(0, ".")

from app.database import AsyncSessionLocal
from app.models.property import Property
from app.models.user import User
from sqlalchemy import select


async def seed_properties():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@thaiestate.com"))
        admin = result.scalar_one_or_none()
        if not admin:
            print("Admin not found. Run seed.py first.")
            return

        result = await db.execute(select(User).where(User.email == "agent@thaiestate.com"))
        agent = result.scalar_one_or_none()

        # Check if properties exist
        result = await db.execute(select(Property).limit(1))
        if result.scalar_one_or_none():
            print("Properties already exist. Skipping.")
            return

        props = [
            Property(
                property_code="BKK-000001", name="Ashton Asoke",
                building_name="Ashton Asoke", address="Sukhumvit 21, Wattana, Bangkok 10110",
                latitude=13.7373, longitude=100.5600, district="Wattana", area="Asoke",
                nearest_bts="Asok", nearest_mrt="Sukhumvit",
                bedroom_count=2, bathroom_count=2, size_sqm=65.0, monthly_rent=35000,
                status="available", pet_allowed=True,
                contact_person="Khun Somsak", contact_line="@somsak", contact_phone="081-234-5678",
                description="Modern condo near BTS Asok, pet-friendly, full facilities",
                tags=["near_bts", "pet_friendly", "pool", "gym", "high_floor"],
                created_by=admin.id, assigned_agent_id=agent.id,
            ),
            Property(
                property_code="BKK-000002", name="Ideo Mobi Sukhumvit 40",
                building_name="Ideo Mobi", address="Sukhumvit 40, Phra Khanong, Bangkok 10110",
                latitude=13.7200, longitude=100.5805, district="Khlong Toei", area="Phra Khanong",
                nearest_bts="Phra Khanong",
                bedroom_count=1, bathroom_count=1, size_sqm=35.0, monthly_rent=18000,
                status="available", pet_allowed=False,
                contact_person="Khun Nong", contact_line="@nong", contact_phone="082-345-6789",
                description="Affordable studio near BTS, ideal for young professionals",
                tags=["near_bts", "affordable", "fitness", "rooftop"],
                created_by=admin.id, assigned_agent_id=agent.id,
            ),
            Property(
                property_code="BKK-000003", name="The Emporio Place",
                building_name="The Emporio", address="Sukhumvit 24, Khlong Toei, Bangkok 10110",
                latitude=13.7305, longitude=100.5680, district="Khlong Toei", area="Phrom Phong",
                nearest_bts="Phrom Phong", nearest_mrt="Sukhumvit",
                bedroom_count=3, bathroom_count=3, size_sqm=120.0, monthly_rent=85000,
                status="available", pet_allowed=True,
                contact_person="Khun Yai", contact_phone="083-456-7890",
                description="Luxury family condo, walking distance to EmQuartier, pool+garden",
                tags=["near_bts", "near_mrt", "pet_friendly", "pool", "garden", "luxury"],
                created_by=admin.id, assigned_agent_id=admin.id,
            ),
            Property(
                property_code="BKK-000004", name="Lumpini Ville Rama 9",
                building_name="Lumpini Ville", address="Rama 9 Road, Huai Khwang, Bangkok 10310",
                latitude=13.7570, longitude=100.5660, district="Huai Khwang", area="Rama 9",
                nearest_mrt="Phra Ram 9",
                bedroom_count=1, bathroom_count=1, size_sqm=28.0, monthly_rent=9000,
                status="available", pet_allowed=False,
                contact_person="Khun Lek", contact_phone="084-567-8901",
                description="Budget-friendly room near MRT Rama 9, covered parking",
                tags=["near_mrt", "budget", "parking"],
                created_by=agent.id, assigned_agent_id=agent.id,
            ),
            Property(
                property_code="BKK-000005", name="The Line Sukhumvit 71",
                building_name="The Line", address="Sukhumvit 71, Wattana, Bangkok 10110",
                latitude=13.7250, longitude=100.5920, district="Wattana", area="Phra Khanong",
                nearest_bts="Phra Khanong",
                bedroom_count=2, bathroom_count=1, size_sqm=48.0, monthly_rent=25000,
                status="pending", pet_allowed=False,
                contact_person="Khun Aoi", contact_line="@aoi", contact_phone="085-678-9012",
                description="Modern 2BR with great BTS access, roof garden, co-working space",
                tags=["near_bts", "coworking", "roof_garden"],
                created_by=agent.id, assigned_agent_id=agent.id,
            ),
            Property(
                property_code="BKK-000006", name="Siamese Exclusive Thonglor",
                building_name="Siamese Exclusive", address="Thonglor Soi 13, Wattana, Bangkok 10110",
                latitude=13.7260, longitude=100.5835, district="Wattana", area="Thonglor",
                nearest_bts="Thong Lo",
                bedroom_count=2, bathroom_count=2, size_sqm=75.0, monthly_rent=55000,
                status="available", pet_allowed=True,
                contact_person="Khun May", contact_line="@may", contact_phone="086-789-0123",
                description="Premium Thonglor residence, Japanese style, pet spa, wine cellar",
                tags=["near_bts", "pet_friendly", "luxury", "pool", "gym"],
                created_by=admin.id, assigned_agent_id=agent.id,
            ),
        ]

        for p in props:
            db.add(p)
        await db.commit()
        print(f"Seeded {len(props)} properties")


if __name__ == "__main__":
    asyncio.run(seed_properties())
