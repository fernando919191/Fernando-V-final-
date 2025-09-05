import secrets
from datetime import datetime, timedelta
from funcionamiento.licencias import crear_licencias
from funcionamiento.usuarios import es_administrador

async def addkeys(update, context):
    """Comando para agregar claves de licencia"""
    user_id = str(update.effective_user.id)
    
    # Verificar si el usuario es admin
    if not es_administrador(user_id):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
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
    
    # Calcular la fecha de expiración
    if tiempo == 'permanente':
        expiracion = 'permanente'
    else:
        ahora = datetime.now()
        if tiempo == '1h':
            expiracion = (ahora + timedelta(hours=1)).isoformat()
        elif tiempo == '1d':
            expiracion = (ahora + timedelta(days=1)).isoformat()
        elif tiempo == '1m':
            expiracion = (ahora + timedelta(days=30)).isoformat()
        elif tiempo == '1y':
            expiracion = (ahora + timedelta(days=365)).isoformat()
    
    # Generar las claves
    licencias_data = []
    claves_generadas = []
    
    for _ in range(cantidad):
        clave = secrets.token_hex(8).upper()
        licencias_data.append({
            'clave': clave,
            'expiracion': expiracion,
            'usada': False,
            'usuario': None,
            'fecha_uso': None
        })
        claves_generadas.append(clave)
    
    # Guardar en la base de datos
    if crear_licencias(licencias_data):
        mensaje = f"✅ Se han generado {cantidad} claves con expiración: {tiempo}\n\n"
        mensaje += "\n".join(claves_generadas)
        await update.message.reply_text(mensaje)
    else:
        await update.message.reply_text("❌ Error al guardar las claves en la base de datos.")