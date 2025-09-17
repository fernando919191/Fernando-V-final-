# comandos/remove.py
import logging
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes

# Configuración de la base de datos
DB_PATH = 'database.db'

logger = logging.getLogger(__name__)

# =========================
# Conexión a la base de datos
# =========================
def get_db_connection():
    """Establece conexión con la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# Funciones de base de datos
# =========================
def obtener_info_usuario_completa(user_id: str) -> dict:
    """Obtiene información completa de un usuario desde la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener información del usuario
        cursor.execute("SELECT * FROM usuarios WHERE user_id = ?", (user_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return {}
        
        usuario_dict = dict(usuario)
        
        # Verificar si tiene licencia activa
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM licencias 
            WHERE user_id = ? AND activa = 1 AND fecha_expiracion > datetime('now')
        """, (user_id,))
        licencia_result = cursor.fetchone()
        
        usuario_dict['es_premium'] = licencia_result['count'] > 0 if licencia_result else False
        
        # Verificar también en la tabla usuarios_premium
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM usuarios_premium 
            WHERE user_id = ? AND activo = 1 AND fecha_expiracion > datetime('now')
        """, (user_id,))
        premium_result = cursor.fetchone()
        
        usuario_dict['tiene_premium_db'] = premium_result['count'] > 0 if premium_result else False
        
        return usuario_dict
        
    except Exception as e:
        logger.error(f"Error obteniendo info usuario {user_id}: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def quitar_usuario_premium(user_id: str) -> bool:
    """Quita el premium de un usuario desactivando sus licencias y actualizando la tabla premium"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Desactivar todas las licencias del usuario
        cursor.execute("""
            UPDATE licencias 
            SET activa = 0 
            WHERE user_id = ? AND activa = 1
        """, (user_id,))
        
        licencias_desactivadas = cursor.rowcount
        
        # Desactivar el registro en la tabla usuarios_premium
        cursor.execute("""
            UPDATE usuarios_premium 
            SET activo = 0 
            WHERE user_id = ? AND activo = 1
        """, (user_id,))
        
        premium_desactivado = cursor.rowcount
        
        # Actualizar el estado premium en la tabla usuarios
        cursor.execute("""
            UPDATE usuarios 
            SET es_premium = 0 
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        
        logger.info(f"Premium removido - Licencias desactivadas: {licencias_desactivadas}, Premium desactivado: {premium_desactivado}")
        
        return licencias_desactivadas > 0 or premium_desactivado > 0
        
    except Exception as e:
        logger.error(f"Error quitando premium a usuario {user_id}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verificar_usuario_premium(user_id: str) -> bool:
    """Verifica si un usuario tiene premium activo en cualquier tabla"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar en licencias
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM licencias 
            WHERE user_id = ? AND activa = 1 AND fecha_expiracion > datetime('now')
        """, (user_id,))
        licencia_result = cursor.fetchone()
        
        # Verificar en usuarios_premium
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM usuarios_premium 
            WHERE user_id = ? AND activo = 1 AND fecha_expiracion > datetime('now')
        """, (user_id,))
        premium_result = cursor.fetchone()
        
        # Verificar en usuarios
        cursor.execute("""
            SELECT es_premium 
            FROM usuarios 
            WHERE user_id = ?
        """, (user_id,))
        usuario_result = cursor.fetchone()
        
        tiene_licencia = licencia_result['count'] > 0 if licencia_result else False
        tiene_premium_db = premium_result['count'] > 0 if premium_result else False
        es_premium_usuario = usuario_result['es_premium'] if usuario_result else False
        
        return tiene_licencia or tiene_premium_db or es_premium_usuario
        
    except Exception as e:
        logger.error(f"Error verificando premium usuario {user_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

# =========================
# Handler principal
# =========================
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para quitar premium a usuarios por user_id"""
    try:
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "📝 Uso: /remove <user_id>\n"
                "Ejemplo: /remove 123456789"
            )
            return
        
        # Obtener user_id objetivo
        target_user_id = context.args[0].strip()
        
        # Validar que el user_id sea numérico
        if not target_user_id.isdigit():
            await update.message.reply_text("❌ El user_id debe ser un número. Ejemplo: /remove 123456789")
            return
        
        # Verificar si el usuario existe en la base de datos
        usuario_info = obtener_info_usuario_completa(target_user_id)
        
        if not usuario_info:
            await update.message.reply_text(f"❌ Usuario con ID {target_user_id} no encontrado en la base de datos.")
            return
        
        # Verificar si el usuario tiene premium activo usando múltiples métodos
        tiene_premium = verificar_usuario_premium(target_user_id)
        
        if not tiene_premium:
            await update.message.reply_text(f"ℹ️ El usuario {target_user_id} no tiene premium activo.")
            return
        
        # Quitar el premium
        exito = quitar_usuario_premium(target_user_id)
        
        if exito:
            # Construir respuesta
            nombre = f"{usuario_info.get('first_name', '')} {usuario_info.get('last_name', '')}".strip()
            username = usuario_info.get('username', 'N/A')
            
            respuesta = (
                f"✅ **Premium Removido Exitosamente**\n\n"
                f"👤 **Usuario ID:** `{target_user_id}`\n"
                f"📛 **Nombre:** {nombre or 'N/A'}\n"
                f"🔖 **Username:** @{username}\n"
                f"🚫 **Estado:** Premium desactivado completamente\n\n"
                f"ℹ️ El usuario ha perdido todos sus beneficios premium."
            )
            await update.message.reply_text(respuesta, parse_mode='Markdown')
            
            # Notificar al usuario si es posible
            try:
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text="🚫 **Aviso Importante**\n\n"
                         "Tu suscripción premium ha sido removida por un administrador.\n"
                         "Has perdido acceso a todos los beneficios premium.\n\n"
                         "Contacta con soporte para más información.",
                    parse_mode='Markdown'
                )
                logger.info(f"✅ Notificación enviada al usuario {target_user_id}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo notificar al usuario {target_user_id}: {e}")
                await update.message.reply_text("✅ Premium removido pero no se pudo notificar al usuario.")
                
        else:
            await update.message.reply_text("❌ Error al remover el premium. No se encontraron licencias activas para desactivar.")
            
    except Exception as e:
        logger.error(f"Error en comando remove: {e}", exc_info=True)
        await update.message.reply_text("❌ Error interno al procesar el comando. Contacta al desarrollador.")

# Función adicional para ver el estado actual del usuario
async def ver_estado_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str):
    """Función auxiliar para ver el estado actual de un usuario"""
    try:
        usuario_info = obtener_info_usuario_completa(user_id)
        tiene_premium = verificar_usuario_premium(user_id)
        
        respuesta = (
            f"📊 **Estado del Usuario**\n\n"
            f"👤 **ID:** `{user_id}`\n"
            f"🎯 **Premium Activo:** {'✅ Sí' if tiene_premium else '❌ No'}\n"
            f"📛 **Nombre:** {usuario_info.get('first_name', 'N/A')} {usuario_info.get('last_name', '')}\n"
            f"🔖 **Username:** @{usuario_info.get('username', 'N/A')}\n"
            f"📅 **Registrado:** {usuario_info.get('fecha_registro', 'N/A')}"
        )
        
        await update.message.reply_text(respuesta, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error mostrando estado usuario {user_id}: {e}")

# =========================
# ¡NO NECESITAS NADA MÁS!
# El sistema automáticamente detectará la función remove()
# y aplicará el decorador comando_con_licencia que incluye
# la verificación de administradores

# =========================
