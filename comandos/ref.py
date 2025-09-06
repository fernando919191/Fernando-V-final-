import logging
from telegram import Update
from telegram.ext import ContextTypes
from index import es_administrador

logger = logging.getLogger(__name__)

async def ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para reenviar mensajes al canal de referencias"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if not es_administrador(user_id, username):
            await update.message.reply_text("❌ Solo administradores pueden usar este comando.")
            return
        
        # Verificar si el mensaje es una respuesta
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "📝 **Uso del comando:**\n\n"
                "1. Responde a un mensaje (con o sin foto)\n"
                "2. Escribe el comando /ref\n"
                "3. El bot reenviará el mensaje al canal de referencias",
                parse_mode='Markdown'
            )
            return
        
        # Obtener el mensaje al que se está respondiendo
        mensaje_original = update.message.reply_to_message
        canal_destino = "@vikingviprefes"  # Canal destino
        
        try:
            # Reenviar el mensaje al canal
            await context.bot.forward_message(
                chat_id=canal_destino,
                from_chat_id=mensaje_original.chat_id,
                message_id=mensaje_original.message_id
            )
            
            # Confirmar al administrador
            await update.message.reply_text(
                f"✅ **Mensaje reenviado exitosamente**\n\n"
                f"📤 **Destino:** {canal_destino}\n"
                f"📝 **Mensaje ID:** `{mensaje_original.message_id}`\n"
                f"👤 **Usuario original:** {mensaje_original.from_user.first_name}",
                parse_mode='Markdown'
            )
            
            logger.info(f"Mensaje {mensaje_original.message_id} reenviado a {canal_destino} por admin {user_id}")
            
        except Exception as e:
            error_msg = str(e).lower()
            if "chat not found" in error_msg:
                await update.message.reply_text(
                    "❌ **Error:** No se pudo encontrar el canal destino.\n"
                    "Verifica que el bot tenga acceso al canal: @vikingviprefes",
                    parse_mode='Markdown'
                )
            elif "bot is not a member" in error_msg:
                await update.message.reply_text(
                    "❌ **Error:** El bot no es miembro del canal.\n"
                    "Asegúrate de que el bot esté agregado como administrador en @vikingviprefes",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ **Error al reenviar:** {e}\n\n"
                    "Verifica los permisos del bot en el canal.",
                    parse_mode='Markdown'
                )
                logger.error(f"Error reenviando mensaje: {e}")
                
    except Exception as e:
        logger.error(f"Error en comando ref: {e}")
        await update.message.reply_text("❌ Error al procesar el comando.")