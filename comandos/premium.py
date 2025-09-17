# comandos/premium.py
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_usuario_por_id, registrar_usuario, actualizar_usuario_premium
from funcionamiento.licencias import activar_licencia_manual
from index import es_administrador
import sqlite3
import os

logger = logging.getLogger(__name__)

# Configuración de la base de datos
DB_PATH = 'database.db'

def get_db_connection():
    """Establece conexión con la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tabla_premium():
    """Crea la tabla de usuarios premium si no existe"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios_premium (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                fecha_activacion DATETIME,
                fecha_expiracion DATETIME,
                dias_licencia INTEGER,
                activo BOOLEAN DEFAULT 1,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Tabla de usuarios premium verificada/creada")
        
    except Exception as e:
        logger.error(f"Error al crear tabla premium: {e}")

# Crear la tabla al importar el módulo
crear_tabla_premium()

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para activar premium a usuarios por user_id"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "Sin username"
        
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
        
        # Validar días
        if dias <= 0:
            await update.message.reply_text("❌ El número de días debe ser mayor a 0")
            return
        
        # Obtener información del usuario objetivo
        usuario_obj = obtener_usuario_por_id(target_user_id)
        
        # Si el usuario no existe en la BD, intentar registrarlo
        if not usuario_obj:
            # Intentar obtener información del usuario de Telegram
            try:
                target_user = await context.bot.get_chat(target_user_id)
                first_name = target_user.first_name or "Usuario"
                last_name = target_user.last_name or ""
                username_tg = target_user.username or "Sin username"
                
                # Registrar usuario en la base de datos
                exito_creacion = registrar_usuario(
                    user_id=target_user_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username_tg
                )
                
                if not exito_creacion:
                    await update.message.reply_text(f"❌ No se pudo crear el usuario con ID: {target_user_id}")
                    return
                
                usuario_obj = obtener_usuario_por_id(target_user_id)
                
            except Exception as e:
                logger.error(f"Error al obtener info del usuario {target_user_id}: {e}")
                await update.message.reply_text(f"❌ No se pudo obtener información del usuario {target_user_id}")
                return
        
        # Activar la licencia en el sistema
        exito_licencia = activar_licencia_manual(target_user_id, dias)
        
        if not exito_licencia:
            await update.message.reply_text("❌ Error al activar la licencia. Contacta al desarrollador.")
            return
        
        # Calcular fechas
        fecha_activacion = datetime.now()
        fecha_expiracion = fecha_activacion + timedelta(days=dias)
        
        # Actualizar usuario como premium
        exito_premium = actualizar_usuario_premium(target_user_id, fecha_expiracion)
        
        if not exito_premium:
            await update.message.reply_text("❌ Error al actualizar estado premium. Contacta al desarrollador.")
            return
        
        # Registrar en la tabla específica de premium
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar si ya existe registro
            cursor.execute('SELECT * FROM usuarios_premium WHERE user_id = ?', (target_user_id,))
            existe = cursor.fetchone()
            
            if existe:
                # Actualizar registro existente
                cursor.execute('''
                    UPDATE usuarios_premium 
                    SET username = ?, first_name = ?, last_name = ?, 
                        fecha_activacion = ?, fecha_expiracion = ?, dias_licencia = ?, activo = 1
                    WHERE user_id = ?
                ''', (
                    usuario_obj.get('username', 'Sin username'),
                    usuario_obj.get('first_name', 'Usuario'),
                    usuario_obj.get('last_name', ''),
                    fecha_activacion,
                    fecha_expiracion,
                    dias,
                    target_user_id
                ))
            else:
                # Insertar nuevo registro
                cursor.execute('''
                    INSERT INTO usuarios_premium 
                    (user_id, username, first_name, last_name, fecha_activacion, fecha_expiracion, dias_licencia)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    target_user_id,
                    usuario_obj.get('username', 'Sin username'),
                    usuario_obj.get('first_name', 'Usuario'),
                    usuario_obj.get('last_name', ''),
                    fecha_activacion,
                    fecha_expiracion,
                    dias
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error al registrar en tabla premium: {e}")
            await update.message.reply_text("⚠️ Premium activado pero error en registro de auditoría.")
        
        # Respuesta de éxito
        respuesta = (
            f"✅ **Premium Activado Exitosamente**\n\n"
            f"👤 **Usuario ID:** `{target_user_id}`\n"
            f"📛 **Nombre:** {usuario_obj.get('first_name', 'N/A')} {usuario_obj.get('last_name', '')}\n"
            f"🔖 **Username:** @{usuario_obj.get('username', 'N/A')}\n"
            f"⏰ **Días:** {dias}\n"
            f"📅 **Activación:** {fecha_activacion.strftime('%Y-%m-%d %H:%M')}\n"
            f"📅 **Expira:** {fecha_expiracion.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"ℹ️ El usuario puede ver su info con /me"
        )
        await update.message.reply_text(respuesta, parse_mode='Markdown')
        
        # Notificar al usuario
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 **¡Felicidades!**\n\n"
                     f"Has recibido **Premium** por {dias} días.\n"
                     f"📅 **Activación:** {fecha_activacion.strftime('%Y-%m-%d %H:%M')}\n"
                     f"📅 **Expira:** {fecha_expiracion.strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"Usa /me para ver tu información completa.\n"
                     f"¡Disfruta de tus beneficios premium! 🚀",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al usuario {target_user_id}: {e}")
            await update.message.reply_text("⚠️ Premium activado pero no se pudo notificar al usuario.")
            
    except ValueError:
        await update.message.reply_text("❌ Formato incorrecto. Uso: /premium <user_id> <días>")
    except Exception as e:
        logger.error(f"Error en comando premium: {e}")
        await update.message.reply_text("❌ Error interno al procesar el comando.")

# Función para verificar si un usuario es premium
def es_usuario_premium(user_id):
    """Verifica si un usuario tiene premium activo"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM usuarios_premium 
            WHERE user_id = ? AND activo = 1 AND fecha_expiracion > datetime('now')
        ''', (user_id,))
        
        usuario = cursor.fetchone()
        conn.close()
        
        return usuario is not None
        
    except Exception as e:
        logger.error(f"Error al verificar usuario premium: {e}")
        return False

# Función para obtener información premium
def obtener_info_premium(user_id):
    """Obtiene información detallada del premium de un usuario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM usuarios_premium 
            WHERE user_id = ? AND activo = 1
        ''', (user_id,))
        
        info = cursor.fetchone()
        conn.close()
        
        if info:
            return dict(info)
        return None
        
    except Exception as e:
        logger.error(f"Error al obtener info premium: {e}")
        return None

# Función para desactivar premium
async def desactivar_premium(context, user_id):
    """Desactiva el premium de un usuario"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE usuarios_premium 
            SET activo = 0 
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Premium desactivado para usuario: {user_id}")
        
        # Notificar al usuario
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ **Tu suscripción premium ha expirado.**\n\n"
                     "Tu acceso a características premium ha finalizado. "
                     "Para renovar, contacta con un administrador.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar expiración a usuario {user_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error al desactivar premium: {e}")
