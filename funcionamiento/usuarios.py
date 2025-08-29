from .database import get_connection
from .licencias import usuario_tiene_licencia_activa
from datetime import datetime

def registrar_usuario(user_id, username=None, first_name=None, last_name=None):
    """Registra o actualiza un usuario en la base de datos"""
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    
    ahora = datetime.now().isoformat()
    tiene_licencia = usuario_tiene_licencia_activa(user_id)
    
    # Insertar o actualizar usuario
    cursor.execute('''
    INSERT OR REPLACE INTO usuarios 
    (user_id, username, first_name, last_name, fecha_registro, tiene_licencia, ultima_verificacion)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, ahora, tiene_licencia, ahora))
    
    conn.commit()
    
    # Obtener el usuario registrado
    cursor.execute('SELECT * FROM usuarios WHERE user_id = ?', (user_id,))
    usuario = cursor.fetchone()
    
    conn.close()
    
    if usuario:
        return dict(usuario)
    return None

def actualizar_estado_licencia(user_id):
    """Actualiza el estado de licencia de un usuario"""
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    
    tiene_licencia = usuario_tiene_licencia_activa(user_id)
    
    cursor.execute('''
    UPDATE usuarios 
    SET tiene_licencia = ?, ultima_verificacion = ?
    WHERE user_id = ?
    ''', (tiene_licencia, datetime.now().isoformat(), user_id))
    
    conn.commit()
    conn.close()
    
    return tiene_licencia

def obtener_usuario(user_id):
    """Obtiene la información de un usuario"""
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM usuarios WHERE user_id = ?', (user_id,))
    usuario = cursor.fetchone()
    
    conn.close()
    
    if usuario:
        return dict(usuario)
    return None

def es_administrador(user_id):
    """Verifica si un usuario es administrador"""
    user_id = str(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM administradores WHERE user_id = ?', (user_id,))
    admin = cursor.fetchone()
    
    conn.close()
    
    return admin is not None

def obtener_todos_usuarios():
    """Obtiene todos los usuarios registrados"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM usuarios')
    usuarios = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return usuarios

def contar_usuarios():
    """Cuenta el total de usuarios registrados"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM usuarios')
    count = cursor.fetchone()['count']
    
    conn.close()
    return count

def contar_usuarios_con_licencia():
    """Cuenta los usuarios con licencia activa"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM usuarios WHERE tiene_licencia = TRUE')
    count = cursor.fetchone()['count']
    
    conn.close()
    return count