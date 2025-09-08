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
# Funciones de base de datos (SIMPLIFICADAS)
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
        
        return usuario_dict
        
    except Exception as e:
        logger.error(f"Error obteniendo info usuario {user_id}: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def quitar_usuario_premium(user_id: str) -> bool:
    """Quita el premium de un usuario desactivando sus licencias"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Desactivar todas las licencias del usuario
        cursor.execute("""
            UPDATE licencias 
            SET activa = 0 
            WHERE user_id = ? AND activa = 1
        """, (user_id,))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"Error quitando premium a usuario {user_id}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# =========================
# Handler principal (¡ESTA ES LA FUNCIÓN QUE BUSCA EL SISTEMA!)
# =========================
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para quitar premium a usuarios por user_id"""
    try:
        # NOTA: La verificación de administrador ya se hace AUTOMÁTICAMENTE
        # por el decorador @comando_con_licencia en index.py
        # ¡No necesitamos verificar is_admin en la base de datos!
        
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
        
        # Obtener información completa del usuario objetivo
        usuario_info = obtener_info_usuario_completa(target_user_id)
        
        if not usuario_info:
            await update.message.reply_text(f"❌ Usuario con ID {target_user_id} no encontrado en la base de datos.")
            return
        
        # Verificar si el usuario tiene premium activo
        if not usuario_info.get('es_premium', False):
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
                f"🚫 **Estado:** Premium desactivado\n\n"
                f"ℹ️ El usuario ha perdido sus beneficios premium."
            )
            await update.message.reply_text(respuesta, parse_mode='Markdown')
            
            # Notificar al usuario si es posible
            try:
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text="🚫 **Aviso Importante**\n\n"
                         "Tu suscripción premium ha sido removida.\n"
                         "Has perdido acceso a los beneficios premium.\n\n"
                         "Contacta con soporte para más información.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"No se pudo notificar al usuario {target_user_id}: {e}")
                
        else:
            await update.message.reply_text("❌ Error al remover el premium. Contacta al desarrollador.")
            
    except Exception as e:
        logger.error(f"Error en comando remove: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al procesar el comando. Verifica la sintaxis.")

# =========================
# ¡NO NECESITAS NADA MÁS!
# El sistema automáticamente detectará la función remove()
# y aplicará el decorador comando_con_licencia que incluye
# la verificación de administradores
# =========================