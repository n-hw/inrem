import asyncio
import argparse
import sys
import os
from uuid import uuid4

# Add app directory to path
sys.path.append(os.getcwd())

from app.db.session import async_session_factory
from app.models.user import User
from app.models.guardian import Guardian
from app.models.monitoring_policy import MonitoringPolicy
from app.core.security import get_password_hash

async def seed_data(ward_email: str, guardian_email: str):
    async with async_session_factory() as db:
        print(f"Creating users: Ward={ward_email}, Guardian={guardian_email}")
        
        # 1. Create Ward
        ward = User(
            id=uuid4(),
            email=ward_email,
            hashed_password=get_password_hash("test1234"),
            full_name="Test Ward",
            fcm_token="dummy_ward_token"
        )
        db.add(ward)
        
        # 2. Create Guardian
        guardian = User(
            id=uuid4(),
            email=guardian_email,
            hashed_password=get_password_hash("test1234"),
            full_name="Test Guardian",
            fcm_token="dummy_guardian_token"
        )
        db.add(guardian)
        
        await db.commit()
        await db.refresh(ward)
        await db.refresh(guardian)
        
        # 3. Create Monitoring Policy for Ward
        policy = MonitoringPolicy(user_id=ward.id)
        db.add(policy)
        
        # 4. Link Guardian
        link = Guardian(
            ward_id=ward.id,
            guardian_id=guardian.id,
            alias="My Ward",
            is_active=True,
            is_accepted=True
        )
        db.add(link)
        
        await db.commit()
        print("✅ Test data seeded successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed test data")
    parser.add_argument("--ward", default="ward@test.com")
    parser.add_argument("--guardian", default="guard@test.com")
    args = parser.parse_args()
    
    asyncio.run(seed_data(args.ward, args.guardian))
