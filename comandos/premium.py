# comandos/premium.py
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_usuario_por_id, registrar_usuario, actualizar_usuario_premium, crear_usuario_basico
from funcionamiento.licencias import activar_licencia_manual
from index import es_administrador

logger = logging.getLogger(__name__)

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para activar premium a usuarios por user_id"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if not es_administrador(user_id, username):
            await update.message.reply_text("❌ Solo administradores pueden usar este comando.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "📝 Uso: /premium <user_id> <días>\n"
                "Ejemplo: /premium 123456789 30\n"
                "Ejemplo: /premium 123456789 30d"
            )
            return
        
        # Obtener user_id objetivo
        target_user_id = context.args[0]
        tiempo_str = context.args[1].lower()
        
        # Validar que el user_id sea numérico
        if not target_user_id.isdigit():
            await update.message.reply_text("❌ El user_id debe ser un número. Ejemplo: /premium 123456789 30")
            return
        
        # Parsear tiempo
        if tiempo_str.endswith('d'):
            dias = int(tiempo_str[:-1])
        else:
            dias = int(tiempo_str)
        
        # PRIMERO crear el usuario si no existe
        usuario_obj = obtener_usuario_por_id(target_user_id)
        
        if not usuario_obj:
            # Crear usuario con información mínima
            try:
                # Intentar obtener información del usuario de Telegram
                try:
                    user_chat = await context.bot.get_chat(target_user_id)
                    first_name = user_chat.first_name or "Usuario"
                    last_name = user_chat.last_name or ""
                    username = user_chat.username or "Sin username"
                except:
                    first_name = "Usuario"
                    last_name = ""
                    username = "Sin username"
                
                # Crear usuario en la base de datos
                crear_usuario_basico(target_user_id, username, first_name, last_name)
                usuario_obj = obtener_usuario_por_id(target_user_id)
                
                if not usuario_obj:
                    await update.message.reply_text(f"❌ No se pudo crear el usuario con ID: {target_user_id}")
                    return
                    
            except Exception as e:
                logger.error(f"Error creando usuario {target_user_id}: {e}")
                await update.message.reply_text(f"❌ Error al crear usuario: {target_user_id}")
                return
        
        # Activar la licencia
        exito = activar_licencia_manual(target_user_id, dias)
        
        if exito:
            fecha_expiracion = datetime.now() + timedelta(days=dias)
            actualizar_usuario_premium(target_user_id, fecha_expiracion)
            
            respuesta = (
                f"✅ **Premium Activado Exitosamente**\n\n"
                f"👤 **Usuario ID:** `{target_user_id}`\n"
                f"📛 **Nombre:** {usuario_obj.get('first_name', 'N/A')} {usuario_obj.get('last_name', '')}\n"
                f"🔖 **Username:** @{usuario_obj.get('username', 'N/A')}\n"
                f"⏰ **Días:** {dias}\n"
                f"📅 **Expira:** {fecha_expiracion.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"ℹ️ El usuario puede ver su info con /me"
            )
            await update.message.reply_text(respuesta, parse_mode='Markdown')
            
            # Notificar al usuario si es posible
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"🎉 **¡Felicidades!**\n\n"
                         f"Has recibido **Premium** por {dias} días.\n"
                         f"📅 **Expira:** {fecha_expiracion.strftime('%Y-%m-%d %H:%M')}\n\n"
                         f"Usa /me para ver tu información completa.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"No se pudo notificar al usuario {target_user_id}: {e}")
                
        else:
            await update.message.reply_text("❌ Error al activar el premium. Contacta al desarrollador.")
            
    except ValueError:
        await update.message.reply_text("❌ Formato incorrecto. Uso: /premium <user_id> <días>")
    except Exception as e:
        logger.error(f"Error en comando premium: {e}")
        await update.message.reply_text("❌ Error al procesar el comando. Verifica la sintaxis.")