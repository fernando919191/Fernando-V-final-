import logging
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_info_usuario_completa, quitar_usuario_premium
from index import es_administrador

logger = logging.getLogger(__name__)

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para quitar premium a usuarios por user_id"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if not es_administrador(user_id, username):
            await update.message.reply_text("❌ Solo administradores pueden usar este comando.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "📝 Uso: /remove <user_id>\n"
                "Ejemplo: /remove 123456789"
            )
            return
        
        # Obtener user_id objetivo
        target_user_id = context.args[0]
        
        # Validar que el user_id sea numérico
        if not target_user_id.isdigit():
            await update.message.reply_text("❌ El user_id debe ser un número. Ejemplo: /remove 123456789")
            return
        
        # Obtener información completa del usuario objetivo
        usuario_info = obtener_info_usuario_completa(target_user_id)
        
        if not usuario_info:
            await update.message.reply_text(f"❌ Usuario con ID {target_user_id} no encontrado en la base de datos.")
            return
        
        # Verificar si el usuario tiene premium activo
        if not usuario_info.get('es_premium', False):
            await update.message.reply_text(f"ℹ️ El usuario {target_user_id} no tiene premium activo.")
            return
        
        # Quitar el premium
        exito = quitar_usuario_premium(target_user_id)
        
        if exito:
            respuesta = (
                f"✅ **Premium Removido Exitosamente**\n\n"
                f"👤 **Usuario ID:** `{target_user_id}`\n"
                f"📛 **Nombre:** {usuario_info.get('first_name', 'N/A')} {usuario_info.get('last_name', '')}\n"
                f"🔖 **Username:** @{usuario_info.get('username', 'N/A')}\n"
                f"🚫 **Estado:** Premium desactivado\n\n"
                f"ℹ️ El usuario ha perdido sus beneficios premium."
            )
            await update.message.reply_text(respuesta, parse_mode='Markdown')
            
            # Notificar al usuario si es posible
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="🚫 **Aviso Importante**\n\n"
                         "Tu suscripción premium ha sido removida.\n"
                         "Has perdido acceso a los beneficios premium.\n\n"
                         "Contacta con soporte para más información.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"No se pudo notificar al usuario {target_user_id}: {e}")
                
        else:
            await update.message.reply_text("❌ Error al remover el premium. Contacta al desarrollador.")
            
    except Exception as e:
        logger.error(f"Error en comando remove: {e}")
        await update.message.reply_text("❌ Error al procesar el comando. Verifica la sintaxis.")