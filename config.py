import os
import logging
from logging.handlers import RotatingFileHandler

# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

# Your API ID & API HASH from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", "25331263"))
API_HASH = os.environ.get("API_HASH", "cab85305bf85125a2ac053210bcd1030")

# Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003508451850"))

# OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", "1955406483"))

# Port
PORT = os.environ.get("PORT", "8585")

# Database
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://ultroidxTeam:ultroidxTeam@cluster0.gabxs6m.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "Cluster0")

# Shortner (token system)
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "inshorturl.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "9f943360c339cec4fed66d9d5cbaa0c2b3d41f81")
VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', 86400))  # 24 hours
IS_VERIFY = os.environ.get("IS_VERIFY", "True") == "True"
TUT_VID = os.environ.get("TUT_VID", "https://t.me/+PZfHvzjSiZc4OGE1")

# Force sub channel id
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "-1003600438841"))

# Workers
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

# Start message
START_MSG = os.environ.get("START_MESSAGE", "Hello {first}\n\nI can store private files in Specified Channel and other users can access it from special link.")

# Admins
try:
    ADMINS = []
    for x in (os.environ.get("ADMINS", "1480923991 5069922547 6695586027").split()):
        ADMINS.append(int(x))
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

# Force sub message
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\n\n<b>You need to join in my Channel/Group to use me\n\nKindly Please join Channel</b>")

# Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "This video/Photo/anything is available on the internet. We LeakHubd or its subsidiary channel doesn't produce any of them.")

# Protect content
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "False") == "True"

# Disable channel button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False") == "True"

# Auto-delete settings
AUTO_DELETE_HOURS = int(os.environ.get("AUTO_DELETE_HOURS", "1"))
AUTO_DELETE_ENABLED = os.environ.get("AUTO_DELETE_ENABLED", "True") == "True"

# Free trial settings
FREE_TRIAL_HOURS = int(os.environ.get("FREE_TRIAL_HOURS", "6"))
FREE_TRIAL_ENABLED = os.environ.get("FREE_TRIAL_ENABLED", "True") == "True"

# Bot stats text
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot!"

# Add owner to admins
ADMINS.append(OWNER_ID)

# Log file
LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
