import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select, and_

# Add app directory to path
sys.path.append(os.getcwd())

from app.db.session import async_session_factory
from app.models.user import User
from app.models.pulse_event import PulseEvent, PulseStage, PulseStatus
from app.services.pulse_engine import check_escalations

async def trigger_escalation(email: str, minutes: int):
    async with async_session_factory() as db:
        # Find user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"❌ User {email} not found")
            return

        # Find Open Soft Check Event
        stmt = select(PulseEvent).where(
            and_(
                PulseEvent.user_id == user.id,
                PulseEvent.status == PulseStatus.OPEN,
                PulseEvent.current_stage == PulseStage.SOFT_CHECK
            )
        )
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        
        if not event:
            print(f"❌ No OPEN Soft Check event found for {email}. Run trigger_soft_check.py first.")
            return

        print(f"Found Event {event.id}. Adjusting timer...")
        
        # Set soft_check_sent_at to past to exceed escalation delay
        # Default delay is usually 60 mins. Let's move it back by 'minutes' + 60
        past_time = datetime.utcnow() - timedelta(minutes=minutes + 60)
        event.soft_check_sent_at = past_time
        
        await db.commit()
        print(f"✅ Event timer advanced. Soft check sent at: {past_time}")
        
        print("🚀 Triggering Escalation Check...")
        escalated = await check_escalations(db)
        
        if escalated:
            print(f"✅ Escalation successful! {len(escalated)} events escalated to GUARDIAN_ALERT.")
        else:
            print("⚠️ No events escalated. Check monitoring policy or delay settings.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger Escalation by modifying event timer")
    parser.add_argument("--email", required=True)
    parser.add_argument("--minutes", type=int, default=60, help="How many minutes past the delay threshold")
    args = parser.parse_args()
    
    asyncio.run(trigger_escalation(args.email, args.minutes))
