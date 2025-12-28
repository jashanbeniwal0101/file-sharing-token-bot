import asyncio
import base64
import logging
import random
import re
import string
import time
from datetime import datetime

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import (
    ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, IS_VERIFY, VERIFY_EXPIRE,
    SHORTLINK_API, SHORTLINK_URL, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT,
    TUT_VID, OWNER_ID, FREE_TRIAL_ENABLED, FREE_TRIAL_HOURS, AUTO_DELETE_ENABLED
)
from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time
from database.database import add_user, del_user, full_userbase, present_user, add_message_tracking, check_free_trial, get_free_trial_time_left, db_update_verify_status
from shortzy import Shortzy

logger = logging.getLogger(__name__)

def format_time(seconds):
    """Format seconds to readable time"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    
    # Check if user exists, if not create with free trial
    if not await present_user(id):
        try:
            await add_user(id)
        except Exception as e:
            logger.error(f"Error adding user {id}: {e}")
    
    verify_status = await get_verify_status(id)
    current_time = time.time()
    
    # Check free trial status
    is_free_trial_active = False
    free_trial_time_left = 0
    
    if FREE_TRIAL_ENABLED:
        is_free_trial_active = await check_free_trial(id)
        if is_free_trial_active:
            free_trial_time_left = await get_free_trial_time_left(id)
    
    # Check verification status
    if verify_status['is_verified'] and VERIFY_EXPIRE < (current_time - verify_status['verified_time']):
        await update_verify_status(id, is_verified=False)

    # Determine if user can access content
    can_access = verify_status['is_verified'] or is_free_trial_active

    if "verify_" in message.text:
        _, token = message.text.split("_", 1)
        if verify_status['verify_token'] != token:
            return await message.reply("Your token is invalid or Expired. Try again by clicking /start")
        await update_verify_status(id, is_verified=True, verified_time=current_time)
        if verify_status["link"] == "":
            reply_markup = None
        await message.reply(f"✅ Your token successfully verified and valid for: 24 Hour", reply_markup=reply_markup, protect_content=False, quote=True)

    elif len(message.text) > 7 and can_access:
        try:
            base64_string = message.text.split(" ", 1)[1]
        except:
            return
        _string = await decode(base64_string)
        argument = _string.split("-")
        
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end+1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        else:
            return
            
        temp_msg = await message.reply("📥 Please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("❌ Something went wrong..!")
            return
        await temp_msg.delete()
        
        snt_msgs = []
        
        for msg in messages:
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                
                # Track message for auto-delete
                if AUTO_DELETE_ENABLED:
                    file_name = msg.document.file_name if msg.document else "Unknown"
                    await add_message_tracking(
                        message_id=snt_msg.id,
                        user_id=id,
                        file_name=file_name,
                        chat_id=message.chat.id
                    )
                
                await asyncio.sleep(0.5)
                snt_msgs.append(snt_msg)
                
            except FloodWait as e:
                await asyncio.sleep(e.value)
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                
                # Track message for auto-delete
                if AUTO_DELETE_ENABLED:
                    file_name = msg.document.file_name if msg.document else "Unknown"
                    await add_message_tracking(
                        message_id=snt_msg.id,
                        user_id=id,
                        file_name=file_name,
                        chat_id=message.chat.id
                    )
                
                snt_msgs.append(snt_msg)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                pass
        
        # Send success message with info
        status_msg = ""
        if is_free_trial_active:
            status_msg = f"\n\n🎁 You're using free trial ({format_time(free_trial_time_left)} left)"
        elif verify_status['is_verified']:
            time_left = VERIFY_EXPIRE - (current_time - verify_status['verified_time'])
            if time_left > 0:
                status_msg = f"\n\n✅ Verified ({get_exp_time(int(time_left))} left)"
        
        if AUTO_DELETE_ENABLED:
            status_msg += f"\n🗑️ Files auto-delete after 24 hours"
        
        if status_msg:
            await message.reply(f"✅ Successfully sent {len(snt_msgs)} file(s){status_msg}")

    elif can_access:
        # Show status and start message
        status_msg = ""
        if is_free_trial_active:
            status_msg = f"\n\n🎁 **Free Trial Active:** {format_time(free_trial_time_left)} remaining\n⚠️ No short links required!"
        elif verify_status['is_verified']:
            time_left = VERIFY_EXPIRE - (current_time - verify_status['verified_time'])
            if time_left > 0:
                status_msg = f"\n\n✅ **Verified:** {get_exp_time(int(time_left))} remaining"
        
        if AUTO_DELETE_ENABLED:
            status_msg += f"\n🗑️ **Auto-Delete:** Enabled (24 hours)"
        
        reply_markup = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("About Me", callback_data="about"),
                InlineKeyboardButton("My Status", callback_data="status"),
                InlineKeyboardButton("Close", callback_data="close")
            ]]
        )
        
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ) + status_msg,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )

    else:
        # User needs verification
        verify_status = await get_verify_status(id)
        
        # Check if free trial was never used
        if FREE_TRIAL_ENABLED and not verify_status.get('free_trial_used'):
            # Activate free trial
            verify_status['free_trial_start'] = current_time
            verify_status['free_trial_used'] = True
            verify_status['trial_expired'] = False
            await db_update_verify_status(id, verify_status)
            
            await message.reply(
                f"🎉 **Welcome! You've activated your {FREE_TRIAL_HOURS}-hour free trial!**\n\n"
                f"⏰ **Free access for:** {FREE_TRIAL_HOURS} hours\n"
                f"🔗 **No short links required** during trial\n"
                f"📁 **Unlimited access** to all files\n\n"
                f"After trial ends, you'll need to verify with short links.\n\n"
                f"Click /start again to begin!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🚀 Start Using", callback_data="start_using")
                ]]),
                quote=True
            )
            return
        
        # Normal verification flow
        if IS_VERIFY and not verify_status['is_verified']:
            short_url = f"adrinolinks.in"
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(id, verify_token=token, link="")
            link = await get_shortlink(
                SHORTLINK_URL,
                SHORTLINK_API,
                f'https://telegram.dog/{client.username}?start=verify_{token}'
            )
            btn = [
                [InlineKeyboardButton("🔗 Click to Verify", url=link)],
                [InlineKeyboardButton('📺 How to use', url=TUT_VID)],
                [InlineKeyboardButton("🔄 Try Again", callback_data="retry_verify")]
            ]
            await message.reply(
                f"**Verification Required**\n\n"
                f"Your free trial has ended. To continue using the bot:\n\n"
                f"1. Click the button below\n"
                f"2. Complete the short link\n"
                f"3. Get 24-hour access\n\n"
                f"⏰ **Token Timeout:** {get_exp_time(VERIFY_EXPIRE)}",
                reply_markup=InlineKeyboardMarkup(btn),
                protect_content=False,
                quote=True
            )

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(
                "Join Channel",
                url=client.invitelink
            )
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='Try Again',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
        disable_web_page_preview=True
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text="⏳ Processing...")
    users = await full_userbase()
    await msg.edit(f"👥 **Total Users:** {len(users)}")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>📢 Broadcasting Message... This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>📊 Broadcast Completed</u>

📈 Total Users: <code>{total}</code>
✅ Successful: <code>{successful}</code>
🚫 Blocked Users: <code>{blocked}</code>
🗑️ Deleted Accounts: <code>{deleted}</code>
❌ Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)
    else:
        msg = await message.reply("❌ Please reply to a message to broadcast")
        await asyncio.sleep(5)
        await msg.delete()

@Bot.on_callback_query(filters.regex("^status$"))
async def status_callback(client: Bot, query: CallbackQuery):
    user_id = query.from_user.id
    verify_status = await get_verify_status(user_id)
    current_time = time.time()
    
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
            status_text += f"🎁 **Free Trial:** Active\n"
            status_text += f"⏰ **Time Left:** {format_time(free_trial_time_left)}\n"
        elif verify_status.get('free_trial_used'):
            status_text += f"🎁 **Free Trial:** Used\n"
        else:
            status_text += f"🎁 **Free Trial:** Available\n"
    
    # Verification info
    if verify_status['is_verified']:
        time_left = VERIFY_EXPIRE - (current_time - verify_status['verified_time'])
        if time_left > 0:
            status_text += f"✅ **Verified:** Yes\n"
            status_text += f"⏰ **Expires in:** {get_exp_time(int(time_left))}\n"
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
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back", callback_data="about"),
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]])
    )

@Bot.on_callback_query(filters.regex("^start_using$"))
async def start_using_callback(client: Bot, query: CallbackQuery):
    await query.message.delete()
    await start_command(client, query.message)
