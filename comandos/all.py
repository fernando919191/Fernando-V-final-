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
        
        # Crear mención de todos los usuarios
        menciones = []
        for usuario in usuarios:
            user_id_str = str(usuario['user_id'])
            first_name = usuario['first_name'] or 'Usuario'
            
            # Crear mención (si tiene username) o mostrar nombre
            if usuario.get('username'):
                menciones.append(f"@{usuario['username']}")
            else:
                menciones.append(f"[{first_name}](tg://user?id={user_id_str})")
        
        # Dividir las menciones en grupos para evitar límites de Telegram
        grupo_menciones = []
        grupo_actual = []
        caracteres_actual = 0
        
        for mencion in menciones:
            # Telegram tiene límite de ~4000 caracteres por mensaje
            if caracteres_actual + len(mencion) + 2 > 4000:
                grupo_menciones.append(grupo_actual)
                grupo_actual = []
                caracteres_actual = 0
            
            grupo_actual.append(mencion)
            caracteres_actual += len(mencion) + 2  # +2 por la coma y espacio
        
        if grupo_actual:
            grupo_menciones.append(grupo_actual)
        
        # Enviar las menciones
        total_usuarios = len(usuarios)
        
        for i, grupo in enumerate(grupo_menciones):
            mensaje = f"📢 **Mención global** - {total_usuarios} usuarios\n\n"
            
            if len(grupo_menciones) > 1:
                mensaje += f"📋 Parte {i + 1} de {len(grupo_menciones)}\n\n"
            
            mensaje += ", ".join(grupo)
            
            await update.message.reply_text(mensaje, parse_mode='Markdown')
        
        # Mensaje de confirmación
        await update.message.reply_text(
            f"✅ **Mención global completada**\n\n"
            f"👥 **Total de usuarios:** {total_usuarios}\n"
            f"📤 **Mensajes enviados:** {len(grupo_menciones)}",
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin {user_id} realizó mención global a {total_usuarios} usuarios")
            
    except Exception as e:
        logger.error(f"Error en comando all: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al realizar la mención global.")