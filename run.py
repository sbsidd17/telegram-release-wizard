
#!/usr/bin/env python3
"""
Simple runner script for the Telegram bot
"""
import asyncio
import sys
import logging
from bot import TelegramBot
from config import BotConfig

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
