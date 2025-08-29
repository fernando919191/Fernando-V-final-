from funcionamiento.usuarios import obtener_usuario, registrar_usuario
from funcionamiento.licencias import obtener_licencias_usuario, usuario_tiene_licencia_activa
from datetime import datetime

async def me(update, context):
    """Muestra la información del usuario actual - Funciona SIN licencia"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    
    # Registrar al usuario si no existe (esto siempre funciona)
    usuario_info = registrar_usuario(user_id, username, first_name, last_name)
    tiene_licencia = usuario_tiene_licencia_activa(user_id)
    
    # Solo intentar obtener licencias si el usuario tiene licencia activa
    licencias = []
    if tiene_licencia:
        licencias = obtener_licencias_usuario(user_id)
    
    # Construir mensaje
    mensaje = "👤 **Tu información**\n\n"
    
    # Información básica
    mensaje += f"🆔 **ID:** {user_id}\n"
    if first_name:
        mensaje += f"👋 **Nombre:** {first_name}"
        if last_name:
            mensaje += f" {last_name}"
        mensaje += "\n"
    if username:
        mensaje += f"📛 **Usuario:** @{username}\n"
    
    # Estado de licencia
    estado_licencia = "✅ **Licencia:** ACTIVA" if tiene_licencia else "❌ **Licencia:** INACTIVA"
    mensaje += f"{estado_licencia}\n"
    
    # Fecha de registro
    if usuario_info and 'fecha_registro' in usuario_info:
        try:
            fecha_registro_str = usuario_info['fecha_registro']
            if 'T' not in fecha_registro_str:
                fecha_registro_str += 'T00:00:00'
            fecha_registro = datetime.fromisoformat(fecha_registro_str.replace('Z', '+00:00'))
            mensaje += f"📅 **Registrado:** {fecha_registro.strftime('%d/%m/%Y %H:%M')}\n"
        except (ValueError, TypeError) as e:
            print(f"Error al parsear fecha de registro: {e}")
    
    # Información de licencias (solo si tiene licencias)
    if licencias:
        mensaje += "\n🔑 **Tus licencias:**\n"
        for i, licencia in enumerate(licencias, 1):
            fecha_uso = licencia.get('fecha_uso', '')
            tiempo_restante = licencia.get('tiempo_restante', 'DESCONOCIDO')
            
            mensaje += f"\n{i}. **Key:** `{licencia.get('clave', 'N/A')}`\n"
            mensaje += f"   ⏰ **Tiempo restante:** {tiempo_restante}\n"
            
            if fecha_uso:
                try:
                    # Asegurar formato correcto de fecha
                    if 'T' not in fecha_uso:
                        fecha_uso += 'T00:00:00'
                    uso_date = datetime.fromisoformat(fecha_uso.replace('Z', '+00:00'))
                    mensaje += f"   🎯 **Activada:** {uso_date.strftime('%d/%m/%Y %H:%M')}\n"
                except (ValueError, TypeError) as e:
                    mensaje += f"   🎯 **Activada:** Error en formato\n"
    elif tiene_licencia:
        mensaje += "\n🔑 **Tienes licencia pero no se encontraron detalles**\n"
    else:
        mensaje += "\n🔑 **No tienes licencias activas**\n"
        mensaje += "Usa `/key <clave>` para activar una licencia\n"
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')