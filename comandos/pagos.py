from telegram import Update
from telegram.ext import ContextTypes

async def pagos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "**Métodos de pago**\n\n"
        "• Binance. 🌐\n"
        "• Zinli. 🌐\n"
        "• Transf. Venezuela. 🇻🇪\n"
        "• Transf. México. 🇲🇽\n"
        "• Paypal. 🌐"
        " "
        "SELLERS AUTORIZADOS.⚠️"
        " "
        "@MR_JACK_SON"
        "@fer889999"
        "@Yayo561 "
        "@yenderx "
        "@Morganbennie "
        "@Ozzwall "
        " "
        "Otra persona que no sea una de ellas, no está autorizada, no nos hacemos cargo de compras falsas
⚠️"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')