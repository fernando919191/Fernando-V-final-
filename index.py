# funcionamiento/index.py

import importlib
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from funcionamiento.tokens import TOKENS
from funcionamiento.config import PREFIX

# Importar comandos
from comandos import start, ping

def main():
    # Seleccionamos el primer token
    token = TOKENS["BOT_1"]

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    # Registrar comandos
    dp.add_handler(CommandHandler("start", start.start))
    
    # Manejo de prefijo con frutas
    def prefijo(update, context):
        text = update.message.text
        if text.startswith(PREFIX + "ping"):
            ping.ping(update, context)

    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prefijo))

    # Iniciar bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
