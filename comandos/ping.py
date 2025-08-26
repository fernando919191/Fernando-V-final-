from telegram import Update
from telegram.ext import ContextTypes
import time

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    message = await update.message.reply_text("🏓 Pong!")  # ✅ AÑADIDO AWAIT
    end_time = time.time()
    response_time = round((end_time - start_time) * 1000, 2)
    await message.edit_text(f"🏓 Pong!\n⏱️ Tiempo: {response_time}ms")  # ✅ AÑADIDO AWAIT