import logging
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_todos_usuarios
from index import es_administrador

logger = logging.getLogger(__name__)

async def all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para etiquetar a todos los usuarios del bot"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if not es_administrador(user_id, username):
            await update.message.reply_text("❌ Solo administradores pueden usar este comando.")
            return
        
        # Obtener todos los usuarios
        usuarios = obtener_todos_usuarios()
        
        if not usuarios:
            await update.message.reply_text("📭 No hay usuarios registrados en el bot.")
            return
        
        # Mensaje simple con estadísticas
        respuesta = (
            f"📢 **Mención global**\n\n"
            f"👥 **Total de usuarios:** {len(usuarios)}\n"
            f"🔔 **Para mencionar:** Usa @all o @everyone\n\n"
            f"💡 *El sistema está listo para la mención*"
        )
        
        await update.message.reply_text(respuesta, parse_mode='Markdown')
        
        logger.info(f"Admin {user_id} usó el comando /all - {len(usuarios)} usuarios")
            
    except Exception as e:
        logger.error(f"Error en comando all: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al ejecutar el comando.")