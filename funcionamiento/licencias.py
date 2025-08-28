import json
import os
from datetime import datetime
from .usuarios import actualizar_estado_licencia

# Ruta al archivo de licencias
LICENCIAS_FILE = os.path.join(os.path.dirname(__file__), '..', 'licencias.json')

def cargar_licencias():
    """Carga las licencias desde el archivo JSON"""
    try:
        with open(LICENCIAS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_licencias(licencias):
    """Guarda las licencias en el archivo JSON"""
    with open(LICENCIAS_FILE, 'w') as f:
        json.dump(licencias, f, indent=4)

def usuario_tiene_licencia_activa(user_id):
    """Verifica si un usuario tiene una licencia activa"""
    user_id = str(user_id)
    licencias = cargar_licencias()
    
    # Buscar en todas las licencias si alguna está activa para este usuario
    for clave, datos in licencias.items():
        if datos['usuario'] == user_id and datos['usada']:
            # Verificar si la licencia es permanente
            if datos['expiracion'] == 'permanente':
                return True
            
            # Verificar si la licencia no ha expirado
            try:
                expiracion = datetime.fromisoformat(datos['expiracion'])
                if datetime.now() < expiracion:
                    return True
            except (ValueError, TypeError):
                continue
    
    return False

def obtener_licencias_usuario(user_id):
    """Obtiene todas las licencias de un usuario"""
    user_id = str(user_id)
    licencias = cargar_licencias()
    licencias_usuario = []
    
    for clave, datos in licencias.items():
        if datos['usuario'] == user_id:
            licencias_usuario.append({
                'clave': clave,
                'expiracion': datos['expiracion'],
                'fecha_uso': datos['fecha_uso']
            })
    
    return licencias_usuario

def canjear_licencia(clave, user_id):
    """Canjea una licencia y actualiza el estado del usuario"""
    user_id = str(user_id)
    licencias = cargar_licencias()
    
    if clave not in licencias:
        return False, "Clave inválida o no existe."
    
    if licencias[clave]['usada']:
        return False, "Esta clave ya ha sido utilizada."
    
    if licencias[clave]['expiracion'] != 'permanente':
        expiracion = datetime.fromisoformat(licencias[clave]['expiracion'])
        if datetime.now() > expiracion:
            return False, "Esta clave ha expirado."
    
    # Canjear la clave
    licencias[clave]['usada'] = True
    licencias[clave]['usuario'] = user_id
    licencias[clave]['fecha_uso'] = datetime.now().isoformat()
    
    guardar_licencias(licencias)
    
    # Actualizar el estado de licencia del usuario
    actualizar_estado_licencia(user_id)
    
    return True, "Licencia activada correctamente."