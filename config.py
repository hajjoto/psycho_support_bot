import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN not found")

if ADMIN_ID is None:
    raise ValueError("ADMIN_ID not found")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL not found")

ADMIN_ID = int(ADMIN_ID)