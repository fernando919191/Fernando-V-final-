# funcionamiento/licencias.py
import sqlite3
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

# ─────────── FUNCIONES DE LICENCIAS ───────────

def crear_tablas():
    """Crea las tablas necesarias si no existen"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Tabla de licencias de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                fecha_activacion TEXT,
                fecha_expiracion TEXT,
                dias INTEGER,
                activa INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
            )
        ''')
        
        # Tabla de keys de licencias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keys_licencias (
                key TEXT PRIMARY KEY,
                dias INTEGER,
                tipo TEXT,
                fecha_creacion TEXT,
                usada INTEGER DEFAULT 0,
                user_id_usada TEXT DEFAULT NULL,
                fecha_uso TEXT DEFAULT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Tablas de licencias verificadas/creadas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        return False

# Crear tablas al importar el módulo
crear_tablas()

def usuario_tiene_licencia_activa(user_id: str) -> bool:
    """Verifica si un usuario tiene licencia activa"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fecha_expiracion FROM licencias 
            WHERE user_id = ? AND activa = 1 AND fecha_expiracion > ?
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        resultado = cursor.fetchone()
        conn.close()
        
        tiene_licencia = resultado is not None
        logger.info(f"🔍 Licencia usuario {user_id}: {'ACTIVA' if tiene_licencia else 'INACTIVA'}")
        return tiene_licencia
        
    except Exception as e:
        logger.error(f"❌ Error en usuario_tiene_licencia_activa: {e}")
        return False

def obtener_info_licencia(user_id: str) -> dict:
    """Obtiene información de la licencia de un usuario"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fecha_activacion, fecha_expiracion, dias, activa 
            FROM licencias WHERE user_id = ?
        ''', (user_id,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'fecha_activacion': resultado[0],
                'fecha_expiracion': resultado[1],
                'dias': resultado[2],
                'activa': resultado[3]
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info licencia: {e}")
        return None

def obtener_tiempo_restante_licencia(user_id: str) -> str:
    """Calcula el tiempo restante de una licencia en formato d-h-m-s"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT fecha_expiracion FROM licencias WHERE user_id = ?', (user_id,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado and resultado[0]:
            expiracion = datetime.strptime(resultado[0], '%Y-%m-%d %H:%M:%S')
            ahora = datetime.now()
            
            if ahora > expiracion:
                return "0d-0h-0m-0s"
            
            diferencia = expiracion - ahora
            dias = diferencia.days
            horas = diferencia.seconds // 3600
            minutos = (diferencia.seconds % 3600) // 60
            segundos = diferencia.seconds % 60
            
            return f"{dias}d-{horas}h-{minutos}m-{segundos}s"
        
        return "0d-0h-0m-0s"
        
    except Exception as e:
        logger.error(f"❌ Error calculando tiempo restante: {e}")
        return "Error"

def activar_licencia_manual(user_id: str, dias: int) -> bool:
    """Activa una licencia manualmente por X días"""
    return agregar_o_sumar_licencia(user_id, dias)

def agregar_o_sumar_licencia(user_id: str, dias: int) -> bool:
    """Si el usuario ya tiene licencia activa, suma los días; si no, crea una nueva."""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Verificar si ya tiene licencia activa y su fecha de expiración
        cursor.execute('SELECT fecha_expiracion, dias FROM licencias WHERE user_id = ? AND activa = 1', (user_id,))
        resultado = cursor.fetchone()

        ahora = datetime.now()
        if resultado and resultado[0]:
            fecha_expiracion_actual = datetime.strptime(resultado[0], '%Y-%m-%d %H:%M:%S')
            if fecha_expiracion_actual > ahora:
                # Sumar días a la fecha de expiración actual
                nueva_expiracion = fecha_expiracion_actual + timedelta(days=dias)
                nuevos_dias = resultado[1] + dias
            else:
                # Licencia vencida, reiniciar desde ahora
                nueva_expiracion = ahora + timedelta(days=dias)
                nuevos_dias = dias
            cursor.execute('''
                UPDATE licencias
                SET fecha_activacion = ?, fecha_expiracion = ?, dias = ?, activa = 1
                WHERE user_id = ?
            ''', (ahora.strftime('%Y-%m-%d %H:%M:%S'), nueva_expiracion.strftime('%Y-%m-%d %H:%M:%S'), nuevos_dias, user_id))
        else:
            # Insertar nueva licencia
            nueva_expiracion = ahora + timedelta(days=dias)
            cursor.execute('''
                INSERT INTO licencias (user_id, fecha_activacion, fecha_expiracion, dias, activa)
                VALUES (?, ?, ?, ?, 1)
            ''', (user_id, ahora.strftime('%Y-%m-%d %H:%M:%S'), nueva_expiracion.strftime('%Y-%m-%d %H:%M:%S'), dias))
        conn.commit()
        conn.close()
        logger.info(f"✅ Licencia sumada/creada: {user_id} +{dias} días")
        return True
    except Exception as e:
        logger.error(f"❌ Error sumando/creando licencia: {e}")
        return False

# ─────────── FUNCIONES DE KEYS ───────────

def guardar_key_en_db(key: str, dias: int, tipo: str) -> bool:
    """Guarda una key de licencia en la base de datos"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Insertar key
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO keys_licencias (key, dias, tipo, fecha_creacion)
            VALUES (?, ?, ?, ?)
        ''', (key, dias, tipo, fecha_actual))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Key guardada: {key} - {dias} días - {tipo}")
        return True
        
    except sqlite3.IntegrityError:
        logger.warning(f"⚠️ Key ya existe: {key}")
        return False
    except Exception as e:
        logger.error(f"❌ Error guardando key: {e}")
        return False

def key_es_valida(key: str) -> tuple:
    """Verifica si una key es válida y no ha sido usada"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, dias, tipo, usada FROM keys_licencias 
            WHERE key = ? AND usada = 0
        ''', (key,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return True, resultado[1], resultado[2]  # Válida, días, tipo
        return False, 0, ""  # No válida
        
    except Exception as e:
        logger.error(f"❌ Error verificando key: {e}")
        return False, 0, ""

def marcar_key_como_usada(key: str, user_id: str) -> bool:
    """Marca una key como usada por un usuario"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        fecha_uso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE keys_licencias 
            SET usada = 1, user_id_usada = ?, fecha_uso = ?
            WHERE key = ?
        ''', (user_id, fecha_uso, key))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Key usada: {key} por usuario: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error marcando key como usada: {e}")
        return False

def obtener_info_key(key: str) -> dict:
    """Obtiene información detallada de una key"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, dias, tipo, fecha_creacion, usada, user_id_usada, fecha_uso
            FROM keys_licencias WHERE key = ?
        ''', (key,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'key': resultado[0],
                'dias': resultado[1],
                'tipo': resultado[2],
                'fecha_creacion': resultado[3],
                'usada': resultado[4],
                'user_id_usada': resultado[5],
                'fecha_uso': resultado[6]
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info key: {e}")
        return None

def obtener_todas_keys() -> list:
    """Obtiene todas las keys de la base de datos"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, dias, tipo, fecha_creacion, usada, user_id_usada, fecha_uso
            FROM keys_licencias ORDER BY fecha_creacion DESC
        ''')
        
        keys = []
        for row in cursor.fetchall():
            keys.append({
                'key': row[0],
                'dias': row[1],
                'tipo': row[2],
                'fecha_creacion': row[3],
                'usada': row[4],
                'user_id_usada': row[5],
                'fecha_uso': row[6]
            })
        
        conn.close()
        return keys
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo todas las keys: {e}")
        return []

def obtener_keys_por_estado(usada: bool = False) -> list:
    """Obtiene keys por estado (usadas o no usadas)"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, dias, tipo, fecha_creacion, user_id_usada, fecha_uso
            FROM keys_licencias WHERE usada = ? ORDER BY fecha_creacion DESC
        ''', (1 if usada else 0,))
        
        keys = []
        for row in cursor.fetchall():
            keys.append({
                'key': row[0],
                'dias': row[1],
                'tipo': row[2],
                'fecha_creacion': row[3],
                'user_id_usada': row[4],
                'fecha_uso': row[5]
            })
        
        conn.close()
        return keys
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo keys por estado: {e}")
        return []

def eliminar_key(key: str) -> bool:
    """Elimina una key de la base de datos"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM keys_licencias WHERE key = ?', (key,))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Key eliminada: {key}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error eliminando key: {e}")
        return False

def obtener_estadisticas_keys() -> dict:
    """Obtiene estadísticas de las keys"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Total keys
        cursor.execute('SELECT COUNT(*) FROM keys_licencias')
        total = cursor.fetchone()[0]
        
        # Keys usadas
        cursor.execute('SELECT COUNT(*) FROM keys_licencias WHERE usada = 1')
        usadas = cursor.fetchone()[0]
        
        # Keys disponibles
        cursor.execute('SELECT COUNT(*) FROM keys_licencias WHERE usada = 0')
        disponibles = cursor.fetchone()[0]
        
        # Keys por tipo
        cursor.execute('''
            SELECT tipo, COUNT(*) FROM keys_licencias 
            GROUP BY tipo
        ''')
        por_tipo = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total': total,
            'usadas': usadas,
            'disponibles': disponibles,
            'por_tipo': por_tipo
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return {}

# ─────────── FUNCIONES DE ADMIN ───────────

def obtener_todas_licencias() -> list:
    """Obtiene todas las licencias activas"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.user_id, u.username, u.first_name, l.fecha_activacion, 
                   l.fecha_expiracion, l.dias, l.activa
            FROM licencias l
            LEFT JOIN usuarios u ON l.user_id = u.user_id
            ORDER BY l.fecha_activacion DESC
        ''')
        
        licencias = []
        for row in cursor.fetchall():
            licencias.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'fecha_activacion': row[3],
                'fecha_expiracion': row[4],
                'dias': row[5],
                'activa': row[6]
            })
        
        conn.close()
        return licencias
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo todas las licencias: {e}")
        return []

def desactivar_licencia(user_id: str) -> bool:
    """Desactiva la licencia de un usuario"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE licencias SET activa = 0 WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Licencia desactivada: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error desactivando licencia: {e}")
        return False

def renovar_licencia(user_id: str, dias_extra: int) -> bool:
    """Renueva la licencia de un usuario agregando días extra"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Obtener fecha actual de expiración
        cursor.execute('SELECT fecha_expiracion FROM licencias WHERE user_id = ?', (user_id,))
        resultado = cursor.fetchone()
        
        if resultado:
            fecha_expiracion_actual = datetime.strptime(resultado[0], '%Y-%m-%d %H:%M:%S')
            nueva_expiracion = fecha_expiracion_actual + timedelta(days=dias_extra)
            
            # Actualizar licencia
            cursor.execute('''
                UPDATE licencias 
                SET fecha_expiracion = ?, dias = dias + ?
                WHERE user_id = ?
            ''', (nueva_expiracion.strftime('%Y-%m-%d %H:%M:%S'), dias_extra, user_id))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Licencia renovada: {user_id} +{dias_extra} días")
            return True
        
        conn.close()
        return False
        
    except Exception as e:
        logger.error(f"❌ Error renovando licencia: {e}")
        return False

def canjear_licencia(user_id: str, key: str) -> tuple:
    """
    Canjea una key de licencia para un usuario.
    Retorna (True, mensaje) si fue exitoso, (False, mensaje) si no.
    """
    try:
        # Verifica si la key es válida y no usada
        valida, dias, tipo = key_es_valida(key)
        if not valida:
            return False, "❌ La key no es válida o ya fue usada."

        # Activa la licencia para el usuario
        exito = agregar_o_sumar_licencia(user_id, dias)
        if not exito:
            return False, "❌ No se pudo activar la licencia."

        # Marca la key como usada
        marcado = marcar_key_como_usada(key, user_id)
        if not marcado:
            return False, "❌ No se pudo marcar la key como usada, pero la licencia fue activada."

        return True, f"✅ Licencia activada por {dias} días usando la key."
    except Exception as e:
        logger.error(f"❌ Error canjeando licencia: {e}")
        return False, "❌ Error interno al canjear la licencia."

def crear_licencias(cantidad: int, dias: int, tipo: str = "default") -> list:
    """
    Crea 'cantidad' de keys de licencia con duración en días y tipo.
    Retorna una lista de keys generadas.
    """
    keys = []
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for _ in range(cantidad):
        key = str(uuid.uuid4()).replace("-", "")[:16]
        cursor.execute('''
            INSERT INTO keys_licencias (key, dias, tipo, fecha_creacion)
            VALUES (?, ?, ?, ?)
        ''', (key, dias, tipo, fecha_actual))
        keys.append(key)
    conn.commit()
    conn.close()
    return keys
