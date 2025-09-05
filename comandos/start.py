from funcionamiento.licencias import usuario_tiene_licencia_activa

async def start(update, context):
    """Mensaje de inicio que verifica la licencia"""
    user_id = update.effective_user.id
    
    # Verificar si el usuario tiene licencia activa
    if usuario_tiene_licencia_activa(user_id):
        mensaje = (
            "¡Hola! 👋 Bienvenido al bot.\n\n"
            "✅ Tu licencia está activa.\n\n"
            "Usa /help para ver los comandos disponibles."
        )
    else:
        mensaje = (
            "¡Hola! 👋 Bienvenido al bot.\n\n"
            "❌ No tienes una licencia activa.\n\n"
            "Para usar el bot, necesitas canjear una clave con /key <clave>\n"
            "Si no tienes una clave, contacta con un administrador."
        )
    
    await update.message.reply_text(mensaje)