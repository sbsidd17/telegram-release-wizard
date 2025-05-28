#!/usr/bin/env python3
"""
Simple runner script for the Telegram bot and Flask app.
"""
import asyncio
import sys
import logging
import signal
import os
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
    logging.getLogger('gunicorn').setLevel(logging.DEBUG)  # Debug for port issues

def signal_handler(signum, frame, loop, bot):
    """Handle shutdown signals gracefully"""
    logger = logging.getLogger(__name__)
    logger.info("Received shutdown signal, stopping bot...")
    
    # Cancel all tasks except the current one
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    # Schedule cleanup in the running loop
    async def cleanup():
        try:
            await bot.client.disconnect()
            await loop.shutdown_asyncgens()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Run cleanup without starting a new loop
    try:
        loop.run_until_complete(cleanup())
    except RuntimeError as e:
        logger.error(f"Error running cleanup: {e}")
    
    # Stop and close the loop
    loop.stop()
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
    sys.exit(0)

async def start_flask():
    """Start the Flask app with Gunicorn in async mode"""
    logger = logging.getLogger(__name__)
    # Use Render's PORT env variable or default to 5000 for Koyeb
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Gunicorn server on port {port}...")
    options = {
        'bind': f'0.0.0.0:{port}',  # Dynamic port for Render compatibility
        'workers': 1,  # Reduced for resource constraints
        'worker_class': 'gthread',  # Threaded workers for async compatibility
        'threads': 1,  # Reduced further for reliability
        'loglevel': 'debug',  # Debug for port issues
        'accesslog': '-',  # Log to stdout
        'errorlog': '-',   # Log to stdout
        'timeout': 120,    # Timeout for health checks
        'graceful_timeout': 30,  # Allow time for connections to close
        'keepalive': 5,  # Keep connections alive for health checks
        'preload_app': True,  # Preload app to reduce startup time
    }
    gunicorn_app = StandaloneApplication(app, options)
    
    # Run Gunicorn in the main thread with asyncio
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, gunicorn_app.run)
    # Wait longer to ensure Gunicorn binds to port
    await asyncio.sleep(10)  # Increased for reliability
    logger.info(f"Gunicorn server started on port {port}")
    return task

async def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    loop = asyncio.get_event_loop()
    
    # Initialize bot early to pass to signal handler
    bot = TelegramBot()
    
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
        # Properly disconnect Telegram client
        if 'bot' in locals():
            try:
                await bot.client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting Telegram client: {e}")
        # Allow time for cleanup
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    # Get the event loop
    loop = asyncio.get_event_loop()
    
    # Initialize bot for signal handler
    bot = TelegramBot()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, loop, bot))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, loop, bot))
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
