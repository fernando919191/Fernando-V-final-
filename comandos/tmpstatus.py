from telegram import Update
from telegram.ext import ContextTypes
from comandos.tmp import tmp_status

async def tmpstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tmp_status(update, context)