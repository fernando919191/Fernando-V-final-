import logging
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_todos_usuarios
from index import es_administrador

logger = logging.getLogger(__name__)

async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # Mensaje inicial
        await update.message.reply_text("📢 **Iniciando mención global...**", parse_mode='Markdown')
        
        total_usuarios = len(usuarios)
        mensajes_enviados = 0
        
        # Dividir usuarios en grupos de 50 para evitar límites
        grupo_size = 50
        for i in range(0, total_usuarios, grupo_size):
            grupo = usuarios[i:i + grupo_size]
            mensaje = "📢 **Mención global**\n\n"
            
            for usuario in grupo:
                user_id_str = str(usuario['user_id'])
                first_name = usuario.get('first_name', 'Usuario')
                
                # Usar mención simple con user_id
                mensaje += f"👤 [{first_name}](tg://user?id={user_id_str})\n"
            
            try:
                await update.message.reply_text(mensaje, parse_mode='Markdown', disable_web_page_preview=True)
                mensajes_enviados += 1
            except Exception as e:
                logger.error(f"Error enviando mensaje de mención: {e}")
                continue
        
        # Mensaje de confirmación
        await update.message.reply_text(
            f"✅ **Mención global completada**\n\n"
            f"👥 **Total de usuarios:** {total_usuarios}\n"
            f"📤 **Mensajes enviados:** {mensajes_enviados}",
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin {user_id} realizó mención global a {total_usuarios} usuarios")
            
    except Exception as e:
        logger.error(f"Error en comando all: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al realizar la mención global.")