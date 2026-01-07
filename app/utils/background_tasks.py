"""
Background task management using asyncio.
Demonstrates async background tasks and event loop concepts.
"""
import asyncio
from typing import Set, Coroutine, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks using asyncio.
    Demonstrates event loop concepts and async task management.
    """
    
    def __init__(self) -> None:
        """Initialize the background task manager."""
        self.tasks: Set[asyncio.Task] = set()
        self.running = False
        self._stop_event = asyncio.Event()
    
    async def start(self) -> None:
        """
        Start the background task manager.
        Creates and manages background tasks in the event loop.
        """
        if self.running:
            logger.warning("BackgroundTaskManager is already running")
            return
        
        self.running = True
        logger.info("🚀 Starting BackgroundTaskManager...")
        logger.info(f"📊 Event loop: {asyncio.get_event_loop()}")
        logger.info(f"🔄 Event loop is running: {asyncio.get_event_loop().is_running()}")
        
        # Start background tasks
        task1 = asyncio.create_task(self._periodic_cleanup_task())
        task2 = asyncio.create_task(self._health_check_task())
        
        self.tasks.add(task1)
        self.tasks.add(task2)
        
        # Wait for stop event
        await self._stop_event.wait()
    
    async def stop(self) -> None:
        """
        Stop all background tasks gracefully.
        Demonstrates proper cleanup in async context.
        """
        if not self.running:
            return
        
        logger.info("🛑 Stopping BackgroundTaskManager...")
        self.running = False
        self._stop_event.set()
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete cancellation
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("✅ BackgroundTaskManager stopped")
    
    async def _periodic_cleanup_task(self) -> None:
        """
        Periodic cleanup task running in the background.
        Demonstrates long-running async background task.
        """
        logger.info("🧹 Starting periodic cleanup task...")
        
        while self.running:
            try:
                # Simulate cleanup work
                await asyncio.sleep(60)  # Run every 60 seconds
                
                if not self.running:
                    break
                
                # Perform cleanup operations
                current_time = datetime.now().isoformat()
                logger.info(f"[{current_time}] 🧹 Running periodic cleanup...")
                
                # Example: Clean up old sessions, cache, etc.
                # This is where you'd implement actual cleanup logic
                
            except asyncio.CancelledError:
                logger.info("🧹 Periodic cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in periodic cleanup task: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _health_check_task(self) -> None:
        """
        Health check task running in the background.
        Demonstrates monitoring background task.
        """
        logger.info("💓 Starting health check task...")
        
        while self.running:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                
                if not self.running:
                    break
                
                # Perform health checks
                current_time = datetime.now().isoformat()
                event_loop = asyncio.get_event_loop()
                
                logger.info(
                    f"[{current_time}] 💓 Health check - "
                    f"Event loop running: {event_loop.is_running()}, "
                    f"Active tasks: {len([t for t in asyncio.all_tasks() if not t.done()])}"
                )
                
            except asyncio.CancelledError:
                logger.info("💓 Health check task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in health check task: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    def add_task(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task[Any]:
        """
        Add a new background task to the manager.
        
        Args:
            coro: Coroutine to run as a background task
            
        Returns:
            The created task
        """
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        
        # Remove task from set when it completes
        task.add_done_callback(self.tasks.discard)
        
        return task

