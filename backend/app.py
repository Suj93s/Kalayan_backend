"""Application entrypoint to run or schedule knowledge updates."""
import argparse
import asyncio
from logger_setup import setup_logging, get_logger
from scheduler import KnowledgeUpdateScheduler
from run_pipeline import main


def main_app():
    setup_logging(logs_dir="logs")
    logger = get_logger()

    parser = argparse.ArgumentParser(description="RAG Backend App")
    parser.add_argument("--run-now", action="store_true", help="Run ingestion immediately and exit")
    parser.add_argument("--start-scheduler", action="store_true", help="Start background scheduler and exit")
    args = parser.parse_args()

    if args.run_now:
        logger.info("Manual run requested")
        main()
        return

    if args.start_scheduler:
        logger.info("Starting scheduler (background)")
        sched = KnowledgeUpdateScheduler()
        sched.start()
        try:
            # Keep process alive
            logger.info("Scheduler is running. Press Ctrl+C to exit.")
            while True:
                asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            sched.stop()
        return

    parser.print_help()


if __name__ == '__main__':
    main_app()
