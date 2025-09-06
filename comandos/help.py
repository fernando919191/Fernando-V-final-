from telegram import Update
from telegram.ext import ContextTypes

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ayuda de comandos"""
    help_text = """
🤖 *COMANDOS DISPONIBLES*:

*/start* - Iniciar el bot. 
*/bin* <6 dígitos> - Consultar información BIN.
*/gen* - Generador de tarjetas.
*/help* - Mostrar esta ayuda.
*/me* - Verifica tu información de usuario.
*/pagos* - Lista de métodos de pago aceptados.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')