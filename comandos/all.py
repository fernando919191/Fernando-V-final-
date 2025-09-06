import logging
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_todos_usuarios
from index import es_administrador

logger = logging.getLogger(__name__)

async def all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if not es_administrador(user_id, username):
            await update.message.reply_text("❌ Solo administradores pueden usar este comando.")
            return
        
        usuarios = obtener_todos_usuarios()
        
        if not usuarios:
            await update.message.reply_text("📭 No hay usuarios registrados.")
            return
        
        # SOLUCIÓN: Usar solo usuarios con username REAL
        menciones = []
        for usuario in usuarios:
            username_real = usuario.get('username', '').strip()
            # Solo agregar si tiene username válido (no vacío y no "Usuario")
            if username_real and username_real.lower() != "usuario":
                menciones.append(f"@{username_real}")
        
        if not menciones:
            await update.message.reply_text("ℹ️ No hay usuarios con username válido para mencionar.")
            return
        
        # Enviar menciones directamente
        mensaje = "📢 **Mención global**\n\n" + " ".join(menciones)
        await update.message.reply_text(mensaje, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error en comando all: {e}")
        await update.message.reply_text("❌ Error en el comando.")