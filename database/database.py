import motor.motor_asyncio
from config import DB_URI, DB_NAME, AUTO_DELETE_HOURS
from datetime import datetime, timedelta
import asyncio

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']
message_data = database['messages']  # New collection for message tracking

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': "",
    'free_trial_start': None,
    'free_trial_used': False,
    'trial_expired': False
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': 0,
            'verify_token': "",
            'link': "",
            'free_trial_start': datetime.now().timestamp(),
            'free_trial_used': True,
            'trial_expired': False
        }
    }

async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return

async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})
    return

# Auto-delete functions
async def add_message_tracking(message_id, user_id, file_name=None, chat_id=None):
    """Track messages for auto-deletion"""
    expire_time = datetime.now() + timedelta(hours=AUTO_DELETE_HOURS)
    message_doc = {
        'message_id': message_id,
        'user_id': user_id,
        'chat_id': chat_id or user_id,  # Store chat_id for deletion
        'file_name': file_name or "Unknown",
        'created_at': datetime.now(),
        'expires_at': expire_time,
        'deleted': False
    }
    await message_data.insert_one(message_doc)
    return message_doc

async def get_expired_messages():
    """Get all messages that have expired"""
    current_time = datetime.now()
    cursor = message_data.find({
        'expires_at': {'$lt': current_time},
        'deleted': False
    })
    messages = await cursor.to_list(length=1000)
    return messages

async def mark_message_deleted(message_id):
    """Mark a message as deleted"""
    await message_data.update_one(
        {'message_id': message_id},
        {'$set': {'deleted': True}}
    )

async def get_user_messages(user_id):
    """Get all messages for a specific user"""
    cursor = message_data.find({'user_id': user_id, 'deleted': False})
    messages = await cursor.to_list(length=100)
    return messages

async def cleanup_old_messages():
    """Clean up messages older than 7 days"""
    week_ago = datetime.now() - timedelta(days=7)
    await message_data.delete_many({'created_at': {'$lt': week_ago}})

# Free trial functions
async def check_free_trial(user_id):
    """Check if user has active free trial"""
    verify_status = await db_verify_status(user_id)
    if not verify_status.get('free_trial_used'):
        return False
    
    free_trial_start = verify_status.get('free_trial_start')
    if not free_trial_start:
        return False
    
    current_time = datetime.now().timestamp()
    free_trial_end = free_trial_start + (6 * 3600)  # 6 hours
    
    if current_time >= free_trial_end:
        # Mark trial as expired
        if not verify_status.get('trial_expired'):
            verify_status['trial_expired'] = True
            await db_update_verify_status(user_id, verify_status)
        return False
    
    return True

async def get_free_trial_time_left(user_id):
    """Get remaining free trial time"""
    verify_status = await db_verify_status(user_id)
    free_trial_start = verify_status.get('free_trial_start')
    
    if not free_trial_start or verify_status.get('trial_expired'):
        return 0
    
    current_time = datetime.now().timestamp()
    free_trial_end = free_trial_start + (6 * 3600)
    
    if current_time >= free_trial_end:
        return 0
    
    return free_trial_end - current_time
