import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8988470317:AAE96QAJoUN2YmCORSCbFUKsYBWkqVnTdyI")
USDT_WALLET = os.getenv("USDT_WALLET", "TPBkTi6MJiUCr9Tshb3U3MY8Ebu1GH9hti")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CURRENCY = "USDT"

ACCOUNT_TYPES = [
    {
        "id": "premium",
        "name": "Premium Reddit Accounts",
        "emoji": "⭐",
        "age": "1 - 5 years",
        "karma": "5,000 - 50,000",
        "price": 40,
        "description": "Aged Reddit accounts with high karma. Perfect for marketing, promotions, and establishing authority in communities."
    },
    {
        "id": "standard",
        "name": "Standard Reddit Accounts",
        "emoji": "🆕",
        "age": "1 - 6 months",
        "karma": "50 - 500",
        "price": 20,
        "description": "Fresh Reddit accounts with growing karma. Great for getting started with Reddit marketing."
    }
]
