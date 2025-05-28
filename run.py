#!/usr/bin/env python3
"""
Simple runner script for the Telegram bot and Flask app.
"""
import asyncio
import sys
import logging
import signal
from bot import TelegramBot
from config import BotConfig
from app import app
import gunicorn.app.base
from gunicorn import config

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """Custom Gunicorn application"""
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        cfg = config.Config()
        for key, value in self.options.items():
            cfg.set(key.lower(), value)

    def load(self):
        return self.application

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from aiohttp and other libraries
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('gunicorn').setLevel(logging.INFO)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger = logging.getLogger(__name__)
    logger.info("Received shutdown signal, stopping bot...")
    sys.exit(0)

async def start_flask():
    """Start the Flask app with Gunicorn in async mode"""
    options = {
        'bind': '0.0.0.0:5000',
        'workers': 1,  # Reduced for Koyeb's resource constraints
        'worker_class': 'gthread',  # Threaded workers for async compatibility
        'threads': 2,  # Reduced for Koyeb's resource constraints
        'loglevel': 'info',
        'accesslog': '-',  # Log to stdout
        'errorlog': '-',   # Log to stdout
        'timeout': 120,    # Timeout for Koyeb compatibility
        'graceful_timeout': 30,  # Allow time for connections to close
        'keepalive': 5,  # Keep connections alive for health checks
        'preload_app': True,  # Corrected from 'preload' to preload app before forking
    }
    gunicorn_app = StandaloneApplication(app, options)
    
    # Run Gunicorn in the main thread with asyncio
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, gunicorn_app.run)
    # Wait briefly to ensure Gunicorn binds to port 5000
    await asyncio.sleep(2)
    return task

async def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load and validate configuration
        config = BotConfig.from_env()
        config.validate()
        
        logger.info("Starting Telegram GitHub Release Uploader Bot...")
        logger.info(f"Target repository: {config.github_repo}")
        logger.info(f"Release tag: {config.github_release_tag}")
        
        # Start Flask app with Gunicorn
        flask_task = await start_flask()
        
        # Start the bot
        bot = TelegramBot()
        await bot.start()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Ensure Gunicorn shuts down gracefully
        if 'flask_task' in locals():
            flask_task.cancel()
            await asyncio.sleep(1)  # Allow time for cleanup

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main())
