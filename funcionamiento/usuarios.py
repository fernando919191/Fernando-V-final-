import sqlite3
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)

def obtener_conexion():
    """Obtiene una conexión a la base de datos con manejo de errores"""
    try:
        conn = sqlite3.connect('database.db', timeout=10)
        conn.execute("PRAGMA busy_timeout = 3000")
        return conn
    except Exception as e:
        logger.error(f"❌ Error al conectar a la base de datos: {e}")
        return None

def sanitizar_texto(texto):
    """Sanitiza texto para evitar problemas en la base de datos"""
    if texto is None:
        return ""
    return str(texto).replace("'", "''").strip()[:100]

def obtener_info_usuario_completa(user_id):
    """Obtiene información completa del usuario, incluyendo premium"""
    conn = obtener_conexion()
    if conn is None:
        return None
        
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, 
                   fecha_registro, ultima_vez_visto, premium_hasta
            FROM usuarios WHERE user_id = ?
        ''', (str(user_id),))
        usuario = cursor.fetchone()
        
        if usuario:
            premium_hasta = usuario[6]
            ahora = datetime.now()
            
            # Verificar si premium_hasta es None o vacío
            if premium_hasta is None or premium_hasta == '':
                es_premium = False
                dias_restantes = 0
            else:
                try:
                    if isinstance(premium_hasta, datetime):
                        dt_premium = premium_hasta
                    else:
                        dt_premium = datetime.strptime(str(premium_hasta), '%Y-%m-%d %H:%M:%S')
                    es_premium = dt_premium > ahora
                    dias_restantes = (dt_premium - ahora).days
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing premium_hasta for user {user_id}: {e}")
                    es_premium = False
                    dias_restantes = 0
            
            return {
                'user_id': usuario[0],
                'username': usuario[1] or "Sin username",
                'first_name': usuario[2] or "",
                'last_name': usuario[3] or "",
                'fecha_registro': usuario[4],
                'ultima_vez_visto': usuario[5],
                'premium_hasta': premium_hasta,
                'es_premium': es_premium,
                'dias_restantes': dias_restantes
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ Error en obtener_info_usuario_completa: {e}")
        return None
    finally:
        if conn:
            conn.close()

def registrar_usuario(user_id, username, first_name, last_name):
    """Registra o actualiza un usuario en la base de datos - Retorna True si fue exitoso"""
    try:
        # Sanitizar datos
        user_id_str = str(user_id)
        username_sanitized = sanitizar_texto(username) or "Sin username"
        first_name_sanitized = sanitizar_texto(first_name)
        last_name_sanitized = sanitizar_texto(last_name)
        
        conn = obtener_conexion()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        # Crear tabla si no existe con mejor estructura
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id TEXT PRIMARY KEY,
                username TEXT DEFAULT 'Sin username',
                first_name TEXT DEFAULT '',
                last_name TEXT DEFAULT '',
                fecha_registro TEXT,
                ultima_vez_visto TEXT,
                premium_hasta TEXT DEFAULT NULL
            )
        ''')
        
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar si el usuario ya existe
        cursor.execute('SELECT user_id FROM usuarios WHERE user_id = ?', (user_id_str,))
        existe = cursor.fetchone()
        
        if existe:
            # Actualizar usuario existente
            cursor.execute('''
                UPDATE usuarios 
                SET username = ?, first_name = ?, last_name = ?, ultima_vez_visto = ?
                WHERE user_id = ?
            ''', (username_sanitized, first_name_sanitized, last_name_sanitized, ahora, user_id_str))
            logger.info(f"📝 Usuario actualizado: {user_id_str}")
        else:
            # Insertar nuevo usuario
            cursor.execute('''
                INSERT INTO usuarios 
                (user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto, premium_hasta)
                VALUES (?, ?, ?, ?, ?, ?, NULL)
            ''', (user_id_str, username_sanitized, first_name_sanitized, last_name_sanitized, ahora, ahora))
            logger.info(f"👤 Nuevo usuario registrado: {user_id_str}")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en registrar_usuario: {e}")
        logger.error(traceback.format_exc())
        return False
    finally:
        if conn:
            conn.close()

def usuario_existe(user_id):
    """Verifica si un usuario existe en la base de datos"""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM usuarios WHERE user_id = ?', (str(user_id),))
        existe = cursor.fetchone()
        return existe is not None
        
    except Exception as e:
        logger.error(f"❌ Error en usuario_existe: {e}")
        return False
    finally:
        if conn:
            conn.close()

def obtener_usuario_por_id(user_id):
    """Devuelve el usuario por su user_id o None si no existe"""
    conn = obtener_conexion()
    if conn is None:
        return None
        
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto 
            FROM usuarios WHERE user_id = ?
        ''', (str(user_id),))
        usuario = cursor.fetchone()
        
        if usuario:
            return {
                'user_id': usuario[0],
                'username': usuario[1] or "Sin username",
                'first_name': usuario[2] or "",
                'last_name': usuario[3] or "",
                'fecha_registro': usuario[4],
                'ultima_vez_visto': usuario[5]
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ Error en obtener_usuario_por_id: {e}")
        return None
    finally:
        if conn:
            conn.close()

def es_administrador(user_id, username=None):
    """Stub: Verifica si el usuario es administrador"""
    # Implementa la lógica real aquí si tienes una lista de admins
    # Por ahora, devolvemos False para todos
    return False

def contar_usuarios():
    """Cuenta el número de usuarios registrados"""
    conn = obtener_conexion()
    if conn is None:
        return 0
        
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios')
        total = cursor.fetchone()[0]
        return total
    except Exception as e:
        logger.error(f"❌ Error en contar_usuarios: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def contar_usuarios_con_licencia():
    """Cuenta el número de usuarios con al menos una licencia activa"""
    conn = obtener_conexion()
    if conn is None:
        return 0
        
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id)
            FROM licencias
            WHERE activa = 1
        ''')
        total = cursor.fetchone()[0]
        return total
    except Exception as e:
        logger.error(f"❌ Error en contar_usuarios_con_licencia: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def crear_usuario_basico(user_id, username=None, first_name=None, last_name=None):
    """Crea un usuario con datos mínimos si no existe"""
    try:
        user_id_str = str(user_id)
        username_sanitized = sanitizar_texto(username) or "Sin username"
        first_name_sanitized = sanitizar_texto(first_name)
        last_name_sanitized = sanitizar_texto(last_name)
        
        conn = obtener_conexion()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios 
            (user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto, premium_hasta)
            VALUES (?, ?, ?, ?, ?, ?, NULL)
        ''', (user_id_str, username_sanitized, first_name_sanitized, last_name_sanitized, ahora, ahora))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en crear_usuario_basico: {e}")
        return False
    finally:
        if conn:
            conn.close()

def obtener_todos_usuarios():
    """Devuelve una lista de todos los usuarios registrados"""
    conn = obtener_conexion()
    if conn is None:
        return []
        
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto 
            FROM usuarios
        ''')
        usuarios = cursor.fetchall()
        
        # Devuelve una lista de diccionarios para facilitar el uso
        return [
            {
                'user_id': row[0],
                'username': row[1] or "Sin username",
                'first_name': row[2] or "",
                'last_name': row[3] or "",
                'fecha_registro': row[4],
                'ultima_vez_visto': row[5]
            }
            for row in usuarios
        ]
    except Exception as e:
        logger.error(f"❌ Error en obtener_todos_usuarios: {e}")
        return []
    finally:
        if conn:
            conn.close()

def actualizar_usuario_premium(user_id, fecha_expiracion):
    """Actualiza la fecha de expiración premium del usuario"""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE usuarios
            SET premium_hasta = ?
            WHERE user_id = ?
        ''', (fecha_expiracion.strftime('%Y-%m-%d %H:%M:%S'), str(user_id)))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error actualizando premium: {e}")
        return False
    finally:
        if conn:
            conn.close()

def quitar_usuario_premium(user_id):
    """Elimina el estado premium de un usuario estableciendo premium_hasta a NULL"""
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE usuarios
            SET premium_hasta = NULL
            WHERE user_id = ?
        ''', (str(user_id),))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en quitar_usuario_premium: {e}")
        return False
    finally:
        if conn:
            conn.close()

def actualizar_estado_licencia(user_id, activa):
    """
    Actualiza el estado de la licencia de un usuario.
    Parámetros:
        user_id: ID del usuario
        activa: 1 (activa) or 0 (inactiva)
    """
    try:
        conn = obtener_conexion()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE licencias
            SET activa = ?
            WHERE user_id = ?
        ''', (int(bool(activa)), str(user_id)))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error actualizando estado de licencia: {e}")
        return False
    finally:
        if conn:
            conn.close()