from pyrogram import __version__
from bot import Bot
from config import OWNER_ID, FREE_TRIAL_ENABLED, AUTO_DELETE_ENABLED
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper_func import get_verify_status
from database.database import check_free_trial, get_free_trial_time_left
import time

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "about":
        extra_info = ""
        
        if FREE_TRIAL_ENABLED:
            extra_info += "\n🎁 **Free Trial:** Enabled (6 hours)"
        
        if AUTO_DELETE_ENABLED:
            extra_info += "\n🗑️ **Auto-Delete:** Enabled (24 hours)"
        
        await query.message.edit_text(
            text=f"<b>🤖 Bot Information</b>\n\n"
                 f"○ Creator: <a href='tg://user?id={OWNER_ID}'>This Person</a>\n"
                 f"○ Language: <code>Python3</code>\n"
                 f"○ Library: <a href='https://docs.pyrogram.org/'>Pyrogram asyncio {__version__}</a>\n"
                 f"○ Channel: @CodeXBotz\n"
                 f"○ Support Group: @CodeXBotzSupport\n"
                 f"{extra_info}\n\n"
                 f"<b>✨ Features:</b>\n"
                 f"• Secure file sharing\n"
                 f"• Link generation\n"
                 f"• User management\n"
                 f"• Auto-cleanup system",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("📊 My Status", callback_data="status"),
                        InlineKeyboardButton("❌ Close", callback_data="close")
                    ]
                ]
            )
        )
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass
    elif data == "status":
        user_id = query.from_user.id
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
            status_text += f"\n🗑️ **Auto-Delete:** Enabled\n"
            status_text += f"⏰ **Delete After:** 24 hours\n"
        
        await query.message.edit_text(
            text=status_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 Back", callback_data="about"),
                    InlineKeyboardButton("❌ Close", callback_data="close")
                ]
            ])
        )
    elif data == "retry_verify":
        await query.message.delete()
        # Resend verification
        from plugins.start import start_command
        await start_command(client, query.message)
