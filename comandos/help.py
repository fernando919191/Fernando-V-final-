from telegram import Update
from telegram.ext import ContextTypes

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ayuda de comandos"""
    help_text = """
🤖 *COMANDOS DISPONIBLES*:

*/start* - Iniciar el bot
*/ping* - Verificar latencia  
*/bin* <6 dígitos> - Consultar información BIN
*/gen* - Generador de tarjetas (conversación)
*/help* - Mostrar esta ayuda

💡 *Ejemplos*:
• `/bin 416916`
• `/ping`
• `/gen` - 4169167362|11|29
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')