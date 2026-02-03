import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select

# Add app directory to path
sys.path.append(os.getcwd())

from app.db.session import async_session_factory
from app.models.user import User
from app.models.activity_signal import ActivitySignal
from app.services.pulse_engine import run_inactivity_check

async def trigger_soft_check(email: str, hours: int):
    async with async_session_factory() as db:
        # Find user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"❌ User {email} not found")
            return

        print(f"⏳ Time Traveling: Setting last active time to {hours} hours ago...")
        
        # Create or update ActivitySignal to be in the past
        # We delete existing signals to ensure clean state or just update the latest one?
        # Simpler: Just ensure there is one signal 'hours' ago.
        
        past_time = datetime.utcnow() - timedelta(hours=hours, minutes=1)
        
        # Check if signal exists
        sig_stmt = select(ActivitySignal).where(ActivitySignal.user_id == user.id)
        sig_result = await db.execute(sig_stmt)
        signal = sig_result.scalar_one_or_none()
        
        if signal:
            signal.last_active_at = past_time
            signal.last_signal_type = "manual_test"
        else:
            signal = ActivitySignal(
                user_id=user.id,
                last_active_at=past_time,
                last_signal_type="manual_test"
            )
            db.add(signal)
            
        await db.commit()
        print(f"✅ User {email} is now 'inactive' (Last active: {past_time})")
        
        print("🚀 Triggering Pulse Engine Inactivity Check...")
        # Force run the check logic
        events = await run_inactivity_check(db)
        print(f"✅ Pulse Engine execution complete. Created {len(events)} events.")
        for e in events:
            print(f"   -> Event Created: {e.id} (Stage: {e.current_stage})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger Soft Check by modifying last active time")
    parser.add_argument("--email", required=True)
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    
    asyncio.run(trigger_soft_check(args.email, args.hours))
