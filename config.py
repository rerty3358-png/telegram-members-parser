import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram API Credentials
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE = os.getenv('PHONE', '')

# Bot Settings
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')
MEMBERS_FILE = os.getenv('MEMBERS_FILE', 'members.json')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Validation
if not API_ID or not API_HASH:
    raise ValueError("API_ID и API_HASH должны быть установлены в файле .env")

if not PHONE:
    raise ValueError("PHONE должен быть установлен в файле .env")
