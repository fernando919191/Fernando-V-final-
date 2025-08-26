# comandos/ping.py

from telegram import Update
from telegram.ext import CallbackContext
import time

def ping(update: Update, context: CallbackContext):
    start_time = time.time()
    message = update.message.reply_text("Pong!")
    end_time = time.time()
    response_time = round((end_time - start_time) * 1000, 2)
    message.edit_text(f"Pong! 🏓\nTiempo de respuesta: {response_time}ms")
