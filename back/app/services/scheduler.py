"""Background scheduler for Guardian Pulse.

Uses asyncio to run periodic tasks without external dependencies.
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable, Coroutine, Any

from app.db.session import async_session
from app.services import pulse_engine

logger = logging.getLogger(__name__)

# Scheduler interval in seconds (10 minutes)
CHECK_INTERVAL_SECONDS = 10 * 60


class PulseScheduler:
    """Background scheduler for running periodic inactivity checks."""
    
    def __init__(self, interval_seconds: int = CHECK_INTERVAL_SECONDS):
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False
    
    async def _run_check(self) -> None:
        """Execute a single inactivity check cycle."""
        try:
            async with async_session() as db:
                events = await pulse_engine.run_inactivity_check(db)
                if events:
                    logger.info(f"[PulseScheduler] Created {len(events)} PulseEvent(s)")
                else:
                    logger.debug("[PulseScheduler] No inactive users detected")
        except Exception as e:
            logger.error(f"[PulseScheduler] Error during check: {e}")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop - runs indefinitely."""
        logger.info(f"[PulseScheduler] Started with interval={self.interval_seconds}s")
        
        while self._running:
            await self._run_check()
            await asyncio.sleep(self.interval_seconds)
    
    def start(self) -> None:
        """Start the background scheduler."""
        if self._running:
            logger.warning("[PulseScheduler] Already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("[PulseScheduler] Scheduler started")
    
    def stop(self) -> None:
        """Stop the background scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("[PulseScheduler] Scheduler stopped")


# Global scheduler instance
pulse_scheduler = PulseScheduler()


async def start_scheduler() -> None:
    """Start the pulse scheduler (called on app startup)."""
    pulse_scheduler.start()


async def stop_scheduler() -> None:
    """Stop the pulse scheduler (called on app shutdown)."""
    pulse_scheduler.stop()
