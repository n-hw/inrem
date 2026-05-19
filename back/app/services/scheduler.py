"""Background schedulers.

Two independent asyncio loops:
- `PulseScheduler` — every 10 min, inactivity-check sweep (Guardian Pulse).
- `AccountPurgeScheduler` — every 24h, hard-delete accounts whose
  30-day grace period elapsed (PIPA 잊혀질 권리, PRD §6 NFR).

No external dependencies — pure asyncio so it works in single-instance
setups. Multi-instance: add a distributed lock (Redis SETNX or Postgres
advisory lock) so only one worker runs each sweep.
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable, Coroutine, Any

from app.db.session import async_session
from app.services import account_service, pulse_engine

logger = logging.getLogger(__name__)

# Scheduler interval in seconds (10 minutes)
CHECK_INTERVAL_SECONDS = 10 * 60

# Account purge sweep interval (24h). 매일 영구 삭제 후보 처리.
PURGE_INTERVAL_SECONDS = 24 * 60 * 60


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


class AccountPurgeScheduler:
    """Sweeps users whose 30-day deletion grace has expired and hard-deletes them.

    Runs once at startup (so a long-down service catches up) and then
    every `interval_seconds` (24h default).
    """

    def __init__(self, interval_seconds: int = PURGE_INTERVAL_SECONDS):
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    async def _run_sweep(self) -> None:
        try:
            async with async_session() as db:
                purged = await account_service.purge_expired_deletions(db)
                if purged:
                    logger.info(
                        "account_purge_sweep_done",
                        extra={"purged_count": len(purged)},
                    )
                else:
                    logger.debug("account_purge_sweep_done (no candidates)")
        except Exception as e:
            logger.error(
                "account_purge_sweep_failed",
                extra={"error": str(e)},
                exc_info=True,
            )

    async def _scheduler_loop(self) -> None:
        logger.info(
            "account_purge_scheduler_started",
            extra={"interval_seconds": self.interval_seconds},
        )
        while self._running:
            await self._run_sweep()
            await asyncio.sleep(self.interval_seconds)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None


# Global scheduler instances
pulse_scheduler = PulseScheduler()
account_purge_scheduler = AccountPurgeScheduler()


async def start_scheduler() -> None:
    """Start background schedulers (called on app startup)."""
    pulse_scheduler.start()
    account_purge_scheduler.start()


async def stop_scheduler() -> None:
    """Stop background schedulers (called on app shutdown)."""
    pulse_scheduler.stop()
    account_purge_scheduler.stop()
