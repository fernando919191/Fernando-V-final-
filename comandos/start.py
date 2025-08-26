# comandos/start.py
from telegram import Update
from telegram.ext import CallbackContext

def start(update: Update, context: CallbackContext):
    update.message.reply_text("¡Hola! Bienvenido a HellBot 🌟")
