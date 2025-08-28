import os
import sys

# Añadir el directorio padre al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from funcionamiento.licencias import canjear_licencia
from funcionamiento.usuarios import registrar_usuario, actualizar_estado_licencia

async def key(update, context):
    """Comando para canjear una clave de licencia"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    
    # Registrar al usuario si no existe
    registrar_usuario(user_id, username, first_name, last_name)
    
    # Verificar los argumentos
    if len(context.args) < 1:
        await update.message.reply_text("❌ Uso: /key <clave>")
        return
    
    clave = context.args[0].upper()
    
    # Canjear la licencia
    success, message = canjear_licencia(clave, user_id)
    
    if success:
        # Actualizar el estado de licencia del usuario
        actualizar_estado_licencia(user_id, True)
        
        # Obtener información de la licencia para mostrar detalles
        from funcionamiento.licencias import cargar_licencias
        licencias = cargar_licencias()
        licencia_info = licencias.get(clave, {})
        
        if licencia_info.get('expiracion') == 'permanente':
            mensaje_final = "✅ ¡Licencia activada! Tienes acceso permanente."
        else:
            expiracion = licencia_info.get('expiracion', '').split('T')[0]
            mensaje_final = f"✅ ¡Licencia activada! Expira el {expiracion}"
    else:
        mensaje_final = f"❌ {message}"
    
    await update.message.reply_text(mensaje_final)