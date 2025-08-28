from funcionamiento.usuarios import obtener_usuario
from funcionamiento.licencias import obtener_licencias_usuario, usuario_tiene_licencia_activa
from datetime import datetime

async def me(update, context):
    """Muestra la información del usuario actual"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    
    # Obtener información de la base de datos (esto actualizará el estado de licencia)
    usuario_info = obtener_usuario(user_id)
    tiene_licencia = usuario_tiene_licencia_activa(user_id)
    licencias = obtener_licencias_usuario(user_id)
    
    # Construir mensaje
    mensaje = "👤 **Tu información**\n\n"
    
    # Información básica
    mensaje += f"🆔 **ID:** `{user_id}`\n"
    if first_name:
        mensaje += f"👋 **Nombre:** {first_name}"
        if last_name:
            mensaje += f" {last_name}"
        mensaje += "\n"
    if username:
        mensaje += f"📛 **Usuario:** @{username}\n"
    
    # Estado de licencia (verificación en tiempo real)
    estado_licencia = "✅ **Licencia:** ACTIVA" if tiene_licencia else "❌ **Licencia:** INACTIVA"
    mensaje += f"{estado_licencia}\n"
    
    # Fecha de registro
    if usuario_info and 'fecha_registro' in usuario_info:
        try:
            fecha_registro = datetime.fromisoformat(usuario_info['fecha_registro'].replace('Z', '+00:00'))
            mensaje += f"📅 **Registrado:** {fecha_registro.strftime('%d/%m/%Y %H:%M')}\n"
        except (ValueError, TypeError):
            pass
    
    # Información de licencias
    if licencias:
        mensaje += "\n🔑 **Tus licencias:**\n"
        for i, licencia in enumerate(licencias, 1):
            expiracion = licencia.get('expiracion', '')
            fecha_uso = licencia.get('fecha_uso', '')
            
            mensaje += f"\n{i}. **Key:** `{licencia.get('clave', 'N/A')}`\n"
            
            if expiracion == 'permanente':
                mensaje += "   ⏰ **Duración:** PERMANENTE\n"
            elif expiracion:
                try:
                    exp_date = datetime.fromisoformat(expiracion.replace('Z', '+00:00'))
                    ahora = datetime.now()
                    if ahora > exp_date:
                        mensaje += "   ⏰ **Estado:** EXPIRADA\n"
                    else:
                        dias_restantes = (exp_date - ahora).days
                        mensaje += f"   ⏰ **Expira:** {exp_date.strftime('%d/%m/%Y')} ({dias_restantes} días restantes)\n"
                except (ValueError, TypeError):
                    mensaje += "   ⏰ **Expiración:** Formato inválido\n"
            
            if fecha_uso:
                try:
                    uso_date = datetime.fromisoformat(fecha_uso.replace('Z', '+00:00'))
                    mensaje += f"   🎯 **Activada:** {uso_date.strftime('%d/%m/%Y %H:%M')}\n"
                except (ValueError, TypeError):
                    pass
    else:
        mensaje += "\n🔑 **No tienes licencias activas**\n"
        mensaje += "Usa `/key <clave>` para activar una licencia\n"
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')