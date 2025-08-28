import json
import os
from datetime import datetime
from funcionamiento.licencias import usuario_tiene_licencia_activa

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
            'tiene_licencia': usuario_tiene_licencia_activa(user_id),
            'ultima_verificacion': datetime.now().isoformat()
        }
    else:
        # Actualizar información existente
        if username is not None:
            usuarios[user_id]['username'] = username
        if first_name is not None:
            usuarios[user_id]['first_name'] = first_name
        if last_name is not None:
            usuarios[user_id]['last_name'] = last_name
        # Actualizar estado de licencia
        usuarios[user_id]['tiene_licencia'] = usuario_tiene_licencia_activa(user_id)
        usuarios[user_id]['ultima_verificacion'] = datetime.now().isoformat()
    
    guardar_usuarios(usuarios)
    return usuarios[user_id]

def actualizar_estado_licencia(user_id):
    """Actualiza el estado de licencia de un usuario basado en verificación real"""
    user_id = str(user_id)
    usuarios = cargar_usuarios()
    
    if user_id in usuarios:
        tiene_licencia = usuario_tiene_licencia_activa(user_id)
        usuarios[user_id]['tiene_licencia'] = tiene_licencia
        usuarios[user_id]['ultima_verificacion'] = datetime.now().isoformat()
        guardar_usuarios(usuarios)
        return tiene_licencia
    
    return False

def obtener_usuario(user_id):
    """Obtiene la información de un usuario y actualiza su estado de licencia"""
    user_id = str(user_id)
    usuarios = cargar_usuarios()
    
    if user_id in usuarios:
        # Actualizar el estado de licencia antes de devolver los datos
        usuarios[user_id]['tiene_licencia'] = usuario_tiene_licencia_activa(user_id)
        usuarios[user_id]['ultima_verificacion'] = datetime.now().isoformat()
        guardar_usuarios(usuarios)
        return usuarios[user_id]
    
    return None

# ... (resto de funciones se mantienen igual)