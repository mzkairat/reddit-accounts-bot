import sys
import os
import json
from flask import Flask, request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from telegram import Update
from src.bot import create_application

app = Flask(__name__)
application = create_application()


@app.route("/", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "Bot is running!", 200
    data = request.get_json()
    if data:
        update = Update.de_json(data, application.bot)
        application.process_update(update)
    return "", 200
