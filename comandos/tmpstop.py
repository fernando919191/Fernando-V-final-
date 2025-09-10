from telegram import Update
from telegram.ext import ContextTypes
from comandos.tmp import tmp_stop

async def tmpstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tmp_stop(update, context)