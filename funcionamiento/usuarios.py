import json
import os
from datetime import datetime

# Ruta al archivo de usuarios
USUARIOS_FILE = os.path.join(os.path.dirname(__file__), '..', 'usuarios.json')

def cargar_usuarios():
    """Carga los usuarios desde el archivo JSON"""
    try:
        with open(USUARIOS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_usuarios(usuarios):
    """Guarda los usuarios en el archivo JSON"""
    with open(USUARIOS_FILE, 'w') as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

def registrar_usuario(user_id, username=None, first_name=None, last_name=None):
    """Registra o actualiza un usuario en la base de datos"""
    user_id = str(user_id)
    usuarios = cargar_usuarios()
    
    # Verificar si el usuario ya existe
    if user_id not in usuarios:
        usuarios[user_id] = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'fecha_registro': datetime.now().isoformat(),
            'tiene_licencia': False,
            'ultima_verificacion': None
        }
    else:
        # Actualizar información existente
        if username is not None:
            usuarios[user_id]['username'] = username
        if first_name is not None:
            usuarios[user_id]['first_name'] = first_name
        if last_name is not None:
            usuarios[user_id]['last_name'] = last_name
    
    guardar_usuarios(usuarios)
    return usuarios[user_id]

def actualizar_estado_licencia(user_id, tiene_licencia):
    """Actualiza el estado de licencia de un usuario"""
    user_id = str(user_id)
    usuarios = cargar_usuarios()
    
    if user_id in usuarios:
        usuarios[user_id]['tiene_licencia'] = tiene_licencia
        usuarios[user_id]['ultima_verificacion'] = datetime.now().isoformat()
        guardar_usuarios(usuarios)
        return True
    
    return False

def obtener_usuario(user_id):
    """Obtiene la información de un usuario"""
    user_id = str(user_id)
    usuarios = cargar_usuarios()
    return usuarios.get(user_id)

def obtener_todos_usuarios():
    """Obtiene todos los usuarios registrados"""
    return cargar_usuarios()

def obtener_usuarios_con_licencia():
    """Obtiene solo los usuarios con licencia activa"""
    usuarios = cargar_usuarios()
    return {uid: data for uid, data in usuarios.items() if data.get('tiene_licencia', False)}

def obtener_usuarios_sin_licencia():
    """Obtiene solo los usuarios sin licencia activa"""
    usuarios = cargar_usuarios()
    return {uid: data for uid, data in usuarios.items() if not data.get('tiene_licencia', False)}

def contar_usuarios():
    """Cuenta el total de usuarios registrados"""
    usuarios = cargar_usuarios()
    return len(usuarios)

def contar_usuarios_con_licencia():
    """Cuenta los usuarios con licencia activa"""
    usuarios = obtener_usuarios_con_licencia()
    return len(usuarios)