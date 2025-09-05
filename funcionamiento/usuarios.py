# funcionamiento/usuarios.py
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def obtener_info_usuario_completa(user_id):
    """Obtiene información completa del usuario, incluyendo premium"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto, premium_hasta
        FROM usuarios WHERE user_id = ?
    ''', (user_id,))
    usuario = cursor.fetchone()
    conn.close()
    if usuario:
        premium_hasta = usuario[6]
        ahora = datetime.now()
        if premium_hasta:
            try:
                dt_premium = datetime.strptime(premium_hasta, '%Y-%m-%d %H:%M:%S')
                es_premium = dt_premium > ahora
                dias_restantes = (dt_premium - ahora).days
            except Exception:
                es_premium = False
                dias_restantes = 0
        else:
            es_premium = False
            dias_restantes = 0
        return {
            'user_id': usuario[0],
            'username': usuario[1],
            'first_name': usuario[2],
            'last_name': usuario[3],
            'fecha_registro': usuario[4],
            'ultima_vez_visto': usuario[5],
            'premium_hasta': premium_hasta,
            'es_premium': es_premium,
            'dias_restantes': dias_restantes
        }
    return None

def registrar_usuario(user_id, username, first_name, last_name):
    """Registra o actualiza un usuario en la base de datos - Retorna True si fue exitoso"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                fecha_registro TEXT,
                ultima_vez_visto TEXT
            )
        ''')
        
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar si el usuario ya existe
        cursor.execute('SELECT user_id FROM usuarios WHERE user_id = ?', (user_id,))
        existe = cursor.fetchone()
        
        if existe:
            # Actualizar usuario existente
            cursor.execute('''
                UPDATE usuarios 
                SET username = ?, first_name = ?, last_name = ?, ultima_vez_visto = ?
                WHERE user_id = ?
            ''', (username, first_name, last_name, ahora, user_id))
            logger.info(f"📝 Usuario actualizado: {user_id}")
        else:
            # Insertar nuevo usuario
            cursor.execute('''
                INSERT INTO usuarios 
                (user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, ahora, ahora))
            logger.info(f"👤 Nuevo usuario registrado: {user_id}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en registrar_usuario: {e}", exc_info=True)
        return False

def usuario_existe(user_id):
    """Verifica si un usuario existe en la base de datos"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM usuarios WHERE user_id = ?', (user_id,))
        existe = cursor.fetchone()
        conn.close()
        
        return existe is not None
        
    except Exception as e:
        logger.error(f"❌ Error en usuario_existe: {e}")
        return False

def obtener_usuario_por_id(user_id):
    """Devuelve el usuario por su user_id o None si no existe"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto FROM usuarios WHERE user_id = ?', (user_id,))
    usuario = cursor.fetchone()
    conn.close()
    if usuario:
        return {
            'user_id': usuario[0],
            'username': usuario[1],
            'first_name': usuario[2],
            'last_name': usuario[3],
            'fecha_registro': usuario[4],
            'ultima_vez_visto': usuario[5]
        }
    return None

def es_administrador(user_id):
    """Stub: Verifica si el usuario es administrador"""
    # Implementa la lógica real aquí si tienes una lista de admins
    return False

def contar_usuarios():
    """Stub: Cuenta el número de usuarios registrados"""
    import sqlite3
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    total = cursor.fetchone()[0]
    conn.close()
    return total

def contar_usuarios_con_licencia():
    """Cuenta el número de usuarios con al menos una licencia activa"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id)
        FROM licencias
        WHERE activa = 1
    ''')
    total = cursor.fetchone()[0]
    conn.close()
    return total

def crear_usuario_basico(user_id, username=None, first_name=None, last_name=None):
    """Crea un usuario con datos mínimos si no existe"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, ahora, ahora))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error en crear_usuario_basico: {e}", exc_info=True)
        return False

def obtener_todos_usuarios():
    """Devuelve una lista de todos los usuarios registrados"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name, last_name, fecha_registro, ultima_vez_visto FROM usuarios')
    usuarios = cursor.fetchall()
    conn.close()
    # Devuelve una lista de diccionarios para facilitar el uso
    return [
        {
            'user_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'fecha_registro': row[4],
            'ultima_vez_visto': row[5]
        }
        for row in usuarios
    ]

def actualizar_usuario_premium(user_id, fecha_expiracion):
    """Actualiza la fecha de expiración premium del usuario"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE usuarios
            SET premium_hasta = ?
            WHERE user_id = ?
        ''', (fecha_expiracion.strftime('%Y-%m-%d %H:%M:%S'), user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando premium: {e}")
        return False

def actualizar_estado_licencia(user_id, activa):
    """
    Actualiza el estado de la licencia de un usuario.
    Parámetros:
        user_id: ID del usuario
        activa: 1 (activa) o 0 (inactiva)
    """
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE licencias
            SET activa = ?
            WHERE user_id = ?
        ''', (int(bool(activa)), user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error actualizando estado de licencia: {e}")
        return False
