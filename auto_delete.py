import asyncio
import logging
from datetime import datetime
from bot import Bot
from database.database import get_expired_messages, mark_message_deleted, cleanup_old_messages
from config import AUTO_DELETE_ENABLED, AUTO_DELETE_HOURS

logger = logging.getLogger(__name__)

class AutoDeleteService:
    def __init__(self):
        self.bot = None
        self.running = False
    
    async def set_bot(self, bot: Bot):
        self.bot = bot
    
    async def delete_expired_messages(self):
        """Delete expired messages from users' chats"""
        if not AUTO_DELETE_ENABLED or not self.bot:
            return
        
        try:
            expired_messages = await get_expired_messages()
            deleted_count = 0
            
            for msg in expired_messages:
                try:
                    message_id = msg['message_id']
                    chat_id = msg['chat_id']
                    
                    # Try to delete the message
                    await self.bot.delete_messages(chat_id, message_id)
                    
                    # Mark as deleted in database
                    await mark_message_deleted(message_id)
                    deleted_count += 1
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    if "MESSAGE_TOO_OLD" not in str(e) and "message to delete not found" not in str(e):
                        logger.warning(f"Failed to delete message {msg['message_id']}: {e}")
                    # Mark as deleted anyway since it might have been deleted manually
                    await mark_message_deleted(msg['message_id'])
            
            if deleted_count > 0:
                logger.info(f"Auto-deleted {deleted_count} messages")
                
            # Cleanup old database entries
            await cleanup_old_messages()
            
        except Exception as e:
            logger.error(f"Error in delete_expired_messages: {e}")
    
    async def start_auto_delete_service(self):
        """Start the auto-delete service"""
        if not AUTO_DELETE_ENABLED:
            logger.info("Auto-delete service is disabled")
            return
        
        self.running = True
        logger.info(f"Auto-delete service started (checking every {AUTO_DELETE_HOURS//2} hours)")
        
        while self.running:
            try:
                await self.delete_expired_messages()
                # Run every half of AUTO_DELETE_HOURS
                await asyncio.sleep(AUTO_DELETE_HOURS * 1800)  # Convert hours to seconds / 2
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-delete loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def stop(self):
        """Stop the auto-delete service"""
        self.running = False
        logger.info("Auto-delete service stopped")

# Global instance
auto_delete_service = AutoDeleteService()
