from telegram import Update
from telegram.ext import ContextTypes

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ayuda de comandos"""
    help_text = """
🤖 *COMANDOS DISPONIBLES*:

*/start* - Iniciar el bot
*/ping* - Verificar latencia  
*/bin* <6 dígitos> - Consultar información BIN
*/help* - Mostrar esta ayuda

💡 *Ejemplos*:
• `/bin 416916`
• `/ping`

🔍 *Nota:* El comando BIN usa APIs públicas que pueden tener límites.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')