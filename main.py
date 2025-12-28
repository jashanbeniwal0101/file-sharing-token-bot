import asyncio
import logging
from bot import Bot
from database.database import cleanup_old_messages

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Cleanup old messages on startup
        logger.info("Starting cleanup of old messages...")
        deleted_count = await cleanup_old_messages()
        logger.info(f"Cleanup completed! Deleted {deleted_count} old messages.")
        
        # Start the bot
        logger.info("Starting bot...")
        bot = Bot()
        await bot.start()
        
        # Keep the bot running
        logger.info("Bot is running!")
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        if 'bot' in locals():
            await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
