import json
import secrets
import os
from datetime import datetime, timedelta

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

async def addkeys(update, context):
    """Comando para agregar claves de licencia"""
    # NOTA: La verificación de permisos ahora se hace en el decorador comando_con_licencia
    # en index.py, por lo que eliminamos la verificación duplicada aquí
    
    # Verificar los argumentos
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /addkeys <cantidad> <tiempo (1h, 1d, 1m, 1y, permanente)>")
        return
    
    try:
        cantidad = int(context.args[0])
        tiempo = context.args[1].lower()
    except ValueError:
        await update.message.reply_text("❌ La cantidad debe ser un número válido.")
        return
    
    # Validar el formato de tiempo
    tiempos_validos = ['1h', '1d', '1m', '1y', 'permanente']
    if tiempo not in tiempos_validos:
        await update.message.reply_text("❌ Tiempo no válido. Usa: 1h, 1d, 1m, 1y o permanente")
        return
    
    # Calcular la fecha de expiración CORREGIDO
    if tiempo == 'permanente':
        expiracion = 'permanente'
    else:
        ahora = datetime.now()
        if tiempo == '1h':
            expiracion = ahora + timedelta(hours=1)
        elif tiempo == '1d':
            expiracion = ahora + timedelta(days=1)
        elif tiempo == '1m':
            expiracion = ahora + timedelta(days=30)  # 30 días para 1 mes
        elif tiempo == '1y':
            expiracion = ahora + timedelta(days=365)  # 365 días para 1 año
        
        # Formatear correctamente la fecha ISO
        expiracion = expiracion.isoformat()
    
    # Generar las claves
    licencias = cargar_licencias()
    claves_generadas = []
    
    for _ in range(cantidad):
        clave = secrets.token_hex(8).upper()  # Genera una clave aleatoria de 16 caracteres
        licencias[clave] = {
            'expiracion': expiracion,
            'usada': False,
            'usuario': None,
            'fecha_uso': None
        }
        claves_generadas.append(clave)
    
    # Guardar las licencias
    guardar_licencias(licencias)
    
    # Enviar mensaje con las claves generadas
    mensaje = f"✅ Se han generado {cantidad} claves con expiración: {tiempo}\n\n"
    mensaje += "\n".join(claves_generadas)
    
    await update.message.reply_text(mensaje)