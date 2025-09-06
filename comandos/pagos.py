from telegram import Update
from telegram.ext import ContextTypes

async def pagos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "**Métodos de pago**\n\n"
        "• Binance. 🌐\n"
        "• Zinli. 🌐\n"
        "• Transf. Venezuela. 🇻🇪\n"
        "• Transf. México. 🇲🇽\n"
        "• Paypal. 🌐\n"
        " \n"
        "SELLERS AUTORIZADOS.⚠️\n"
        " \n"
        "@MR_JACK_SON\n"
        "@fer889999\n"
        "@Yayo561\n"
        "@yenderx\n"
        "@Morganbennie\n"
        "@Ozzwall\n"
        " "
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')