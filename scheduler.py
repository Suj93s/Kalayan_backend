"""Automatic update scheduler using APScheduler."""

import json
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from logger_setup import get_logger


class KnowledgeUpdateScheduler:
    """Manages automatic website crawling and knowledge base updates."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.scheduler = BackgroundScheduler()
        self.logger = get_logger()
        self._setup_jobs()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def _setup_jobs(self) -> None:
        """Setup scheduled jobs based on config."""
        if not self.config.get("scheduler", {}).get("enabled", False):
            self.logger.info("Scheduler is disabled in config.")
            return
        
        scheduler_config = self.config["scheduler"]
        hour = scheduler_config.get("update_hour", 2)
        minute = scheduler_config.get("update_minute", 0)
        
        # Add cron job for daily update
        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(
            func=self._run_update,
            trigger=trigger,
            id="daily_knowledge_update",
            name="Daily Knowledge Base Update",
            replace_existing=True
        )
        
        self.logger.info(f"Scheduled daily update at {hour:02d}:{minute:02d} UTC")
    
    def _run_update(self) -> None:
        """Run the update process (called by scheduler)."""
        self.logger.info("=" * 60)
        self.logger.info("Starting scheduled knowledge base update")
        self.logger.info("=" * 60)
        
        try:
            # Import here to avoid circular imports
            from run_pipeline import main
            main()
            self.logger.info("=" * 60)
            self.logger.info("Scheduled update completed successfully")
            self.logger.info("=" * 60)
        except Exception as e:
            self.logger.error(f"Error during scheduled update: {e}", exc_info=True)
            self.logger.info("=" * 60)
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.scheduler.running:
            self.logger.warning("Scheduler is already running.")
            return
        
        self.scheduler.start()
        self.logger.info("Scheduler started (background mode)")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.scheduler.running:
            self.logger.warning("Scheduler is not running.")
            return
        
        self.scheduler.shutdown()
        self.logger.info("Scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running
