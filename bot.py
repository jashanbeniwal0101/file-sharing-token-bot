from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
import asyncio
import logging

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL, CHANNEL_ID, PORT, AUTO_DELETE_ENABLED, AUTO_DELETE_HOURS
import pyrogram.utils

pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

logger = logging.getLogger(__name__)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER
        self.auto_delete_task = None

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        if FORCE_SUB_CHANNEL:
            try:
                link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                    link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                self.LOGGER(__name__).warning(f"Please Double check the FORCE_SUB_CHANNEL value and Make sure Bot is Admin in channel with Invite Users via Link Permission, Current Force Sub Channel Value: {FORCE_SUB_CHANNEL}")
                self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/ultroid_official for support")
                sys.exit()
        
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(f"Error occurred: {e}")
            self.LOGGER(__name__).warning(f"Make sure bot is Admin in DB Channel, and Double-check the CHANNEL_ID value.")
            self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/ultroid_official for support")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/ultroid_official")
        self.LOGGER(__name__).info(f""" \n\n       
(っ◔◡◔)っ ♥ ULTROIDOFFICIAL ♥
░╚════╝░░╚════╝░╚═════╝░╚══════╝
                                          """)
        self.username = usr_bot_me.username
        
        # Start auto-delete service if enabled
        if AUTO_DELETE_ENABLED:
            self.auto_delete_task = asyncio.create_task(self.start_auto_delete_service())
            self.LOGGER(__name__).info(f"Auto-delete service started (every {AUTO_DELETE_HOURS//2} hours)")
        
        # Web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def start_auto_delete_service(self):
        """Background task to auto-delete expired messages"""
        from database.database import get_expired_messages, mark_message_deleted, cleanup_old_messages
        
        while True:
            try:
                if AUTO_DELETE_ENABLED:
                    expired_messages = await get_expired_messages()
                    deleted_count = 0
                    
                    for msg in expired_messages:
                        try:
                            message_id = msg['message_id']
                            chat_id = msg.get('chat_id', msg['user_id'])
                            
                            # Try to delete the message
                            await self.delete_messages(chat_id, message_id)
                            
                            # Mark as deleted in database
                            await mark_message_deleted(message_id)
                            deleted_count += 1
                            
                            await asyncio.sleep(0.1)  # Small delay
                            
                        except Exception as e:
                            # Message might already be deleted or not found
                            await mark_message_deleted(msg['message_id'])
                    
                    if deleted_count > 0:
                        self.LOGGER(__name__).info(f"Auto-deleted {deleted_count} expired messages")
                    
                    # Cleanup old database entries
                    await cleanup_old_messages()
                
                # Run every 12 hours (half of AUTO_DELETE_HOURS)
                await asyncio.sleep(AUTO_DELETE_HOURS * 1800)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.LOGGER(__name__).error(f"Error in auto-delete service: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def stop(self, *args):
        if self.auto_delete_task:
            self.auto_delete_task.cancel()
            try:
                await self.auto_delete_task
            except asyncio.CancelledError:
                pass
        
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")
