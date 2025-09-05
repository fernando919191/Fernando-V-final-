# comandos/key.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.licencias import key_es_valida, marcar_key_como_usada, activar_licencia_manual
from funcionamiento.usuarios import registrar_usuario
from index import es_administrador

logger = logging.getLogger(__name__)

async def key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para canjear keys de licencia"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        
        # Registrar usuario
        registrar_usuario(user_id, username, first_name, last_name)
        
        # Verificar argumentos
        if not context.args:
            await update.message.reply_text(
                "🔑 *Sistema de Licencias*\n\n"
                "Para canjear una key usa:\n"
                "`/key <tu_key>` o `.key <tu_key>`\n\n"
                "💡 Las keys las genera un administrador con `.genkey`",
                parse_mode="Markdown"
            )
            return
        
        key = context.args[0].strip().upper()
        
        # Verificar si la key es válida
        valida, dias, tipo = key_es_valida(key)
        
        if not valida:
            await update.message.reply_text(
                "❌ Key inválida o ya usada.\n\n"
                "Verifica que:\n"
                "• La key esté escrita correctamente\n"
                "• No haya sido usada antes\n"
                "• Sea una key válida\n\n"
                "Contacta con un administrador si necesitas una key."
            )
            return
        
        # Activar licencia con la key
        exito = activar_licencia_manual(user_id, dias)
        
        if exito:
            # Marcar key como usada
            marcar_key_como_usada(key, user_id)
            
            tipo_texto = {
                "30d": "30 días",
                "perm": "PERMANENTE", 
                "7d": "7 días",
                "90d": "90 días"
            }.get(tipo, f"{dias} días")
            
            await update.message.reply_text(
                f"🎉 *¡Licencia activada!*\n\n"
                f"✅ Key canjeada exitosamente\n"
                f"👤 Usuario: {first_name or ''} {last_name or ''}\n"
                f"🆔 ID: {user_id}\n"
                f"⏰ Duración: {tipo_texto}\n"
                f"🔑 Key: `{key}`\n\n"
                f"¡Disfruta de todos los beneficios del bot!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Error al activar la licencia.\n"
                "Contacta con un administrador."
            )
            
    except Exception as e:
        logger.error(f"Error en comando key: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al procesar la key.")