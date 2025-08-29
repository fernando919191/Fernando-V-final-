from .database import get_connection
from datetime import datetime

def calcular_tiempo_restante(expiracion_str):
    """Calcula el tiempo restante de forma legible"""
    if expiracion_str == 'permanente':
        return "PERMANENTE"
    
    try:
        expiracion = datetime.fromisoformat(expiracion_str)
        ahora = datetime.now()
        
        if ahora > expiracion:
            return "EXPIRADA"
        
        diferencia = expiracion - ahora
        segundos_totales = diferencia.total_seconds()
        
        # Calcular años, días, horas, minutos
        años = int(segundos_totales // (365 * 24 * 3600))
        segundos_restantes = segundos_totales % (365 * 24 * 3600)
        
        dias = int(segundos_restantes // (24 * 3600))
        segundos_restantes %= (24 * 3600)
        
        horas = int(segundos_restantes // 3600)
        segundos_restantes %= 3600
        
        minutos = int(segundos_restantes // 60)
        
        # Formatear según el tiempo restante
        if años > 0:
            return f"{años} año(s), {dias} día(s), {horas} hora(s)"
        elif dias > 0:
            return f"{dias} día(s), {horas} hora(s), {minutos} minuto(s)"
        elif horas > 0:
            return f"{horas} hora(s), {minutos} minuto(s)"
        else:
            return f"{minutos} minuto(s)"
            
    except (ValueError, TypeError):
        return "FORMATO INVÁLIDO"

def usuario_tiene_licencia_activa(user_id):
    """Verifica si un usuario tiene una licencia activa"""
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM licencias 
    WHERE usuario = ? AND usada = TRUE 
    AND (expiracion = 'permanente' OR expiracion > ?)
    ''', (user_id, datetime.now().isoformat()))
    
    licencia = cursor.fetchone()
    conn.close()
    
    return licencia is not None

def obtener_licencias_usuario(user_id):
    """Obtiene todas las licencias de un usuario"""
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT clave, expiracion, fecha_uso FROM licencias 
    WHERE usuario = ?
    ''', (user_id,))
    
    licencias = []
    for row in cursor.fetchall():
        tiempo_restante = calcular_tiempo_restante(row['expiracion'])
        licencias.append({
            'clave': row['clave'],
            'expiracion': row['expiracion'],
            'fecha_uso': row['fecha_uso'],
            'tiempo_restante': tiempo_restante
        })
    
    conn.close()
    return licencias

def canjear_licencia(clave, user_id):
    """Canjea una licencia y devuelve (éxito, mensaje)"""
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si la licencia existe
    cursor.execute('SELECT * FROM licencias WHERE clave = ?', (clave,))
    licencia = cursor.fetchone()
    
    if not licencia:
        conn.close()
        return False, "Clave inválida o no existe."
    
    if licencia['usada']:
        conn.close()
        return False, "Esta clave ya ha sido utilizada."
    
    # Verificar expiración (si no es permanente)
    if licencia['expiracion'] != 'permanente':
        try:
            expiracion_dt = datetime.fromisoformat(licencia['expiracion'])
            if datetime.now() > expiracion_dt:
                conn.close()
                return False, "Esta clave ha expirado."
        except (ValueError, TypeError):
            conn.close()
            return False, "Error en el formato de expiración."
    
    # Canjear la licencia
    cursor.execute('''
    UPDATE licencias 
    SET usada = TRUE, usuario = ?, fecha_uso = ?
    WHERE clave = ?
    ''', (user_id, datetime.now().isoformat(), clave))
    
    conn.commit()
    conn.close()
    
    return True, "Licencia activada correctamente."

def crear_licencias(licencias_data):
    """Crea múltiples licencias en la base de datos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for licencia in licencias_data:
            cursor.execute('''
            INSERT OR REPLACE INTO licencias (clave, expiracion, usada, usuario, fecha_uso)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                licencia['clave'],
                licencia['expiracion'],
                licencia['usada'],
                licencia['usuario'],
                licencia['fecha_uso']
            ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creando licencias: {e}")
        return False
    finally:
        conn.close()