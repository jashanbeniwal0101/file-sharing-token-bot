from pyrogram import filters
from pyrogram.types import Message
from bot import Bot
from config import ADMINS, BOT_STATS_TEXT, USER_REPLY_TEXT, AUTO_DELETE_ENABLED, FREE_TRIAL_ENABLED
from datetime import datetime
from helper_func import get_readable_time
from database.database import add_user, present_user, get_user_messages
from helper_func import get_verify_status
from database.database import check_free_trial, get_free_trial_time_left
import time

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

@Bot.on_message(filters.command('stats') & filters.user(ADMINS))
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    uptime = get_readable_time(delta.seconds)
    
    # Get additional stats
    from database.database import full_userbase, message_data
    users = await full_userbase()
    total_messages = await message_data.count_documents({})
    active_messages = await message_data.count_documents({'deleted': False})
    
    stats_text = BOT_STATS_TEXT.format(uptime=uptime)
    stats_text += f"\n\n📊 **Additional Stats:**\n"
    stats_text += f"👥 **Total Users:** {len(users)}\n"
    stats_text += f"📁 **Total Messages Tracked:** {total_messages}\n"
    stats_text += f"📂 **Active Messages:** {active_messages}\n"
    
    if AUTO_DELETE_ENABLED:
        stats_text += f"🗑️ **Auto-Delete:** Enabled\n"
    
    if FREE_TRIAL_ENABLED:
        stats_text += f"🎁 **Free Trial:** Enabled\n"
    
    await message.reply(stats_text)

@Bot.on_message(filters.command('mystatus') & filters.private)
async def my_status(client: Bot, message: Message):
    user_id = message.from_user.id
    
    # Check if user exists
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass
    
    verify_status = await get_verify_status(user_id)
    
    # Check free trial
    is_free_trial_active = False
    free_trial_time_left = 0
    
    if FREE_TRIAL_ENABLED:
        is_free_trial_active = await check_free_trial(user_id)
        if is_free_trial_active:
            free_trial_time_left = await get_free_trial_time_left(user_id)
    
    # Build status message
    status_text = "👤 **Your Account Status**\n\n"
    
    # Free trial info
    if FREE_TRIAL_ENABLED:
        if is_free_trial_active:
            status_text += f"✅ **Free Trial:** Active\n"
            status_text += f"⏰ **Time Left:** {format_time(free_trial_time_left)}\n"
        elif verify_status.get('free_trial_used'):
            status_text += f"❌ **Free Trial:** Used\n"
        else:
            status_text += f"🎁 **Free Trial:** Available\n"
    
    # Verification info
    if verify_status['is_verified']:
        time_left = 86400 - (time.time() - verify_status['verified_time'])
        if time_left > 0:
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            status_text += f"✅ **Verified:** Yes\n"
            status_text += f"⏰ **Expires in:** {hours}h {minutes}m\n"
        else:
            status_text += f"✅ **Verified:** Expired\n"
    else:
        status_text += f"❌ **Verified:** No\n"
    
    # Auto-delete info
    if AUTO_DELETE_ENABLED:
        user_messages = await get_user_messages(user_id)
        status_text += f"\n🗑️ **Auto-Delete:** Enabled\n"
        status_text += f"📁 **Your Files:** {len(user_messages)} stored\n"
        status_text += f"⏰ **Delete After:** 24 hours\n"
    
    await message.reply(status_text)

@Bot.on_message(filters.private & filters.incoming)
async def useless(_, message: Message):
    id = message.from_user.id
    
    if id in ADMINS:
        return
    
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    
    if USER_REPLY_TEXT:
        await message.reply(USER_REPLY_TEXT)
