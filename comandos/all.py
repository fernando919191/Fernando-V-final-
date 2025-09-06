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
        
        total_usuarios = len(usuarios)
        
        # Crear las menciones directamente
        menciones = []
        for usuario in usuarios:
            user_id_str = str(usuario['user_id'])
            first_name = usuario.get('first_name', 'Usuario')
            username_str = usuario.get('username', '')
            
            if username_str:
                # Si tiene username, usar @mention
                menciones.append(f"@{username_str}")
            else:
                # Si no tiene username, usar link con user_id
                menciones.append(f"[{first_name}](tg://user?id={user_id_str})")
        
        # Dividir en grupos de 40 menciones por mensaje (límite de Telegram)
        grupo_size = 40
        mensajes_enviados = 0
        
        for i in range(0, len(menciones), grupo_size):
            grupo = menciones[i:i + grupo_size]
            mensaje = f"📢 **Mención global** - {total_usuarios} usuarios\n\n"
            mensaje += " • ".join(grupo)
            
            await update.message.reply_text(mensaje, parse_mode='Markdown', disable_web_page_preview=True)
            mensajes_enviados += 1
        
        # Mensaje de confirmación final
        await update.message.reply_text(
            f"✅ **Mención completada**\n"
            f"👥 **Total:** {total_usuarios} usuarios\n"
            f"📤 **Mensajes:** {mensajes_enviados}",
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin {user_id} mencionó a {total_usuarios} usuarios")
            
    except Exception as e:
        logger.error(f"Error en comando all: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al realizar la mención.")