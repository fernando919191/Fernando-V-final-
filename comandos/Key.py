import json
import os
from datetime import datetime

# Ruta al archivo de licencias
LICENCIAS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'licencias.json')

def cargar_licencias():
    """Carga las licencias desde el archivo JSON"""
    try:
        with open(LICENCIAS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_licencias(licencias):
    """Guarda las licencias en el archivo JSON"""
    with open(LICENCIAS_FILE, 'w') as f:
        json.dump(licencias, f, indent=4)

async def key(update, context):
    """Comando para canjear una clave de licencia"""
    user_id = str(update.effective_user.id)
    
    # Verificar los argumentos
    if len(context.args) < 1:
        await update.message.reply_text("❌ Uso: /key <clave>")
        return
    
    clave = context.args[0].upper()
    
    # Cargar licencias
    licencias = cargar_licencias()
    
    # Verificar si la clave existe
    if clave not in licencias:
        await update.message.reply_text("❌ Clave inválida o no existe.")
        return
    
    # Verificar si la clave ya fue usada
    if licencias[clave]['usada']:
        await update.message.reply_text("❌ Esta clave ya ha sido utilizada.")
        return
    
    # Verificar si la clave ha expirado (si no es permanente)
    if licencias[clave]['expiracion'] != 'permanente':
        expiracion = datetime.fromisoformat(licencias[clave]['expiracion'])
        if datetime.now() > expiracion:
            await update.message.reply_text("❌ Esta clave ha expirado.")
            return
    
    # Canjear la clave
    licencias[clave]['usada'] = True
    licencias[clave]['usuario'] = user_id
    licencias[clave]['fecha_uso'] = datetime.now().isoformat()
    
    # Guardar los cambios
    guardar_licencias(licencias)
    
    # Determinar el tipo de licencia
    expiracion = licencias[clave]['expiracion']
    if expiracion == 'permanente':
        mensaje = "✅ ¡Licencia activada! Tienes acceso permanente."
    else:
        mensaje = f"✅ ¡Licencia activada! Expira el {expiracion.split('T')[0]}"
    
    await update.message.reply_text(mensaje)