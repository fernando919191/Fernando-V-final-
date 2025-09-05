# comandos/me.py
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_info_usuario_completa, registrar_usuario
from funcionamiento.licencias import usuario_tiene_licencia_activa, obtener_tiempo_restante_licencia
from index import es_administrador

logger = logging.getLogger(__name__)

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información detallada del usuario - Registra automáticamente si no existe"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Sin username"
        first_name = update.effective_user.first_name or ""
        last_name = update.effective_user.last_name or ""
        
        logger.info(f"🔍 Ejecutando comando /me para usuario: {user_id}")
        
        # Registrar usuario primero (esto crea la tabla si no existe)
        registro_exitoso = registrar_usuario(user_id, username, first_name, last_name)
        
        if not registro_exitoso:
            await update.message.reply_text("❌ Error al registrar tu usuario. Contacta con un administrador.")
            return
        
        # Obtener información completa
        info_usuario = obtener_info_usuario_completa(user_id)
        
        if not info_usuario:
            await update.message.reply_text("❌ No se pudo obtener tu información. Contacta con un administrador.")
            return
        
        # Determinar si tiene licencia activa
        tiene_licencia = usuario_tiene_licencia_activa(user_id)
        logger.info(f"📊 Licencia usuario {user_id}: {'ACTIVA' if tiene_licencia else 'INACTIVA'}")
        
        # Obtener días restantes de premium
        tiempo_restante = "0d-0h-0m-0s"
        if info_usuario['es_premium'] and info_usuario.get('premium_hasta'):
            try:
                dt_premium = datetime.strptime(info_usuario['premium_hasta'], '%Y-%m-%d %H:%M:%S')
                delta = dt_premium - datetime.now()
                days = delta.days
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                tiempo_restante = f"{days}d-{hours}h-{minutes}m-{seconds}s"
            except Exception:
                tiempo_restante = "0d-0h-0m-0s"
        else:
            # Si no es premium, puedes dejarlo en cero o mostrar lo que ya tienes
            tiempo_restante = "0d-0h-0m-0s"

        # Formatear fecha de registro
        fecha_registro = info_usuario.get('fecha_registro', datetime.now())
        
        if isinstance(fecha_registro, str):
            try:
                fecha_registro = datetime.strptime(fecha_registro, '%Y-%m-%d %H:%M:%S')
            except:
                fecha_registro = datetime.now()
        
        fecha_formateada = fecha_registro.strftime('%d/%m/%y - %I:%M%p').lower()
        
        # Plan y estado basado en información de usuario
        if info_usuario['es_premium']:
            plan = "Premium"
            status = "Active ✅"
        else:
            plan = "Free"
            status = "Inactive ❌"
        
        # Construir respuesta
        respuesta = f"""
≜ - Get Info › User
- - - - - - - - - - - - - - -
⋄ User : {first_name} {last_name} - {user_id}
⋄ Username : @{username} 
⋄ Rank : [{'Admin 👑' if es_administrador(user_id, username) else 'User 👤'}]  |  BannedϞ No
⋄ Status : {status}
- - - - - - - - - - - - - - -
⋄ Plan : {plan} 🎯
⋄ Days : {tiempo_restante}
⋄ Regist: {fecha_formateada}
- - - - - - - - - - - - - - -
💡 Usa /help para ver comandos disponibles
"""
        
        logger.info(f"✅ Información mostrada exitosamente para usuario: {user_id}")
        await update.message.reply_text(respuesta)
        
    except Exception as e:
        logger.error(f"❌ Error crítico en comando me: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al obtener tu información. Contacta con un administrador.")