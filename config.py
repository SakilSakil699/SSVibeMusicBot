import os

class Config:
    API_ID = int(os.environ.get("API_ID", "1234567"))  # Apni Telegram API ID
    API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")  # Apna API Hash
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")  # BotFather Token
    SUDO_USERS = [123456789]  # Apni Telegram User ID (aur chahein toh Samina ki ID bhi add kar sakte hain)
    
    # Public & Brand Identity
    BOT_NAME = "SS Vibe Music"
    BOT_USERNAME = "SSVibeMusicBot"
