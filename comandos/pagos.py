from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.config import PREFIX

async def pagos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "**Métodos de pago**\n\n"
        "• Binance. 🌐\n"
        "• Zinli. 🌐\n"
        "• Transf. Venezuela. 🇻🇪\n"
        "• Transf. México. 🇲🇽\n"
        "• Paypal. 🌐"
    )
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# Si usas handlers con decorators o necesitas exportar la función
def get_handler():
    from telegram.ext import CommandHandler
    return CommandHandler('pagos', pagos_command)