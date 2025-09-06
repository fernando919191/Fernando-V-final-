import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_info_usuario_completa, registrar_usuario, reparar_tabla_usuarios
from index import es_administrador

logger = logging.getLogger(__name__)

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra información detallada del usuario"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Sin username"
        first_name = update.effective_user.first_name or ""
        last_name = update.effective_user.last_name or ""
        
        logger.info(f"🔍 Ejecutando comando /me para usuario: {user_id}")
        
        # Asegurar que la tabla esté correcta
        reparar_tabla_usuarios()
        
        # Registrar/actualizar usuario
        registro_exitoso = registrar_usuario(user_id, username, first_name, last_name)
        
        if not registro_exitoso:
            await update.message.reply_text("❌ Error al registrar tu usuario. Contacta con un administrador.")
            return
        
        # Obtener información completa
        info_usuario = obtener_info_usuario_completa(user_id)
        
        if not info_usuario:
            await update.message.reply_text("❌ No se pudo obtener tu información. Contacta con un administrador.")
            return
        
        # Determinar estado premium
        es_premium = info_usuario.get('es_premium', False)
        premium_hasta = info_usuario.get('premium_hasta')
        
        # Calcular tiempo restante si es premium
        tiempo_restante = "0d-0h-0m-0s"
        if es_premium and premium_hasta:
            try:
                if isinstance(premium_hasta, str):
                    dt_premium = datetime.strptime(premium_hasta, '%Y-%m-%d %H:%M:%S')
                else:
                    dt_premium = premium_hasta
                
                ahora = datetime.now()
                if dt_premium > ahora:
                    delta = dt_premium - ahora
                    days = delta.days
                    hours, remainder = divmod(delta.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    tiempo_restante = f"{days}d-{hours}h-{minutes}m-{seconds}s"
                else:
                    tiempo_restante = "0d-0h-0m-0s"
                    es_premium = False  # Actualizar estado si ya expiró
                    
            except Exception as e:
                logger.warning(f"Error calculando tiempo premium para {user_id}: {e}")
                tiempo_restante = "0d-0h-0m-0s"
                es_premium = False
        
        # Formatear fecha de registro
        fecha_registro = info_usuario.get('fecha_registro')
        fecha_formateada = "Desconocida"
        
        if fecha_registro:
            try:
                if isinstance(fecha_registro, str):
                    fecha_dt = datetime.strptime(fecha_registro, '%Y-%m-%d %H:%M:%S')
                else:
                    fecha_dt = fecha_registro
                fecha_formateada = fecha_dt.strftime('%d/%m/%y - %I:%M%p').lower()
            except Exception:
                fecha_formateada = "Desconocida"
        
        # Determinar plan y estado
        if es_premium:
            plan = "Premium 🎯"
            status = "Active ✅"
        else:
            plan = "Free 🎯"
            status = "Inactive ❌"
        
        # Verificar si es administrador
        es_admin = es_administrador(user_id, username)
        
        # Construir respuesta
        respuesta = f"""
≜ - Get Info › User
- - - - - - - - - - - - - - -
⋄ User : {first_name} {last_name} - {user_id}
⋄ Username : @{username} 
⋄ Rank : [{'Admin 👑' if es_admin else 'User 👤'}]  |  BannedϞ No
⋄ Status : {status}
- - - - - - - - - - - - - - -
⋄ Plan : {plan}
⋄ Days : {tiempo_restante}
⋄ Regist: {fecha_formateada}
- - - - - - - - - - - - - - -
💡 Usa /help para ver comandos disponibles
"""
        
        logger.info(f"✅ Información mostrada para usuario: {user_id} - Premium: {es_premium}")
        await update.message.reply_text(respuesta)
        
    except Exception as e:
        logger.error(f"❌ Error crítico en comando me: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al obtener tu información. Contacta con un administrador.")