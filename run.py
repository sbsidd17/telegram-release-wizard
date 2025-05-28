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
from threading import Thread
from app import app
import gunicorn.app.base
from gunicorn import config
from gunicorn.arbiter import Arbiter

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

def start_flask():
    """Start the Flask app with Gunicorn"""
    options = {
        'bind': '0.0.0.0:5000',
        'workers': 2,  # Adjust based on your needs
        'loglevel': 'info',
        'accesslog': '-',  # Log to stdout
        'errorlog': '-',   # Log to stdout
    }
    StandaloneApplication(app, options).run()

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

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger = logging.getLogger(__name__)
    logger.info("Received shutdown signal, stopping bot...")
    sys.exit(0)

async def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Start Flask app in a separate thread
    flask_thread = Thread(target=start_flask)
    flask_thread.start()
    
    try:
        # Load and validate configuration
        config = BotConfig.from_env()
        config.validate()
        
        logger.info("Starting Telegram GitHub Release Uploader Bot...")
        logger.info(f"Target repository: {config.github_repo}")
        logger.info(f"Release tag: {config.github_release_tag}")
        
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

if __name__ == "__main__":
    asyncio.run(main())
