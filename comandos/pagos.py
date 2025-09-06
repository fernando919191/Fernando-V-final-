from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.config import PREFIX

async def pagos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "<b>Métodos de pago</b>\n\n"
        "• Binance. 🌐\n"
        "• Zinli. 🌐\n"
        "• Transf. Venezuela. 🇻🇪\n"
        "• Transf. México. 🇲🇽\n"
        "• Paypal. 🌐"
    )
    
    await update.message.reply_text(mensaje, parse_mode='HTML')

def get_handler():
    from telegram.ext import CommandHandler
    return CommandHandler('pagos', pagos_command)