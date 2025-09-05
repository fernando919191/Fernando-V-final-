from funcionamiento.usuarios import contar_usuarios, contar_usuarios_con_licencia, obtener_todos_usuarios

async def users(update, context):
    """Muestra estadísticas de usuarios"""
    user_id = str(update.effective_user.id)
    
    # Solo el admin principal puede usar este comando
    if user_id != "6751216122":
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    total_usuarios = contar_usuarios()
    usuarios_con_licencia = contar_usuarios_con_licencia()
    usuarios_sin_licencia = total_usuarios - usuarios_con_licencia
    
    mensaje = (
        "📊 **Estadísticas de Usuarios**\n\n"
        f"👥 Total de usuarios: {total_usuarios}\n"
        f"✅ Con licencia activa: {usuarios_con_licencia}\n"
        f"❌ Sin licencia: {usuarios_sin_licencia}\n"
        f"📈 Porcentaje con licencia: {round((usuarios_con_licencia/total_usuarios)*100, 2) if total_usuarios > 0 else 0}%"
    )
    
    await update.message.reply_text(mensaje)