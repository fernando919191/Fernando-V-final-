import os
import json
from datetime import datetime
from .licencias import usuario_tiene_licencia_activa

# Ruta al archivo de usuarios
USUARIOS_FILE = os.path.join(os.path.dirname(__file__), '..', 'usuarios.txt')

def cargar_usuarios():
    """Carga los usuarios desde el archivo TXT"""
    usuarios = {}
    try:
        with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    user_id, datos_str = line.split(':', 1)
                    # Convertir string JSON a diccionario
                    try:
                        usuarios[user_id] = json.loads(datos_str)
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        # Si el archivo no existe, se creará automáticamente al guardar
        pass
    except Exception as e:
        print(f"Error cargando usuarios: {e}")
    return usuarios

def guardar_usuarios(usuarios):
    """Guarda los usuarios en el archivo TXT"""
    try:
        with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
            for user_id, datos in usuarios.items():
                # Formato: user_id:{json_data}
                linea = f"{user_id}:{json.dumps(datos, ensure_ascii=False)}\n"
                f.write(linea)
        return True
    except Exception as e:
        print(f"Error guardando usuarios: {e}")
        return False

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
    
    if guardar_usuarios(usuarios):
        return usuarios[user_id]
    else:
        return None

def actualizar_estado_licencia(user_id):
    """Actualiza el estado de licencia de un usuario"""
    user_id = str(user_id)
    usuarios = cargar_usuarios()
    
    if user_id in usuarios:
        tiene_licencia = usuario_tiene_licencia_activa(user_id)
        usuarios[user_id]['tiene_licencia'] = tiene_licencia
        usuarios[user_id]['ultima_verificacion'] = datetime.now().isoformat()
        
        if guardar_usuarios(usuarios):
            return tiene_licencia
    
    return False

def obtener_usuario(user_id):
    """Obtiene la información de un usuario"""
    user_id = str(user_id)
    usuarios = cargar_usuarios()
    return usuarios.get(user_id)

# ... (mantener las otras funciones igual)