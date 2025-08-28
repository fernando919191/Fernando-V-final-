import json
import os
from datetime import datetime

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
    """Verifica si un usuario tiene una licencia activa - CORREGIDO"""
    user_id = str(user_id)
    licencias = cargar_licencias()
    
    # Buscar en todas las licencias si alguna está activa para este usuario
    for clave, datos in licencias.items():
        if datos.get('usuario') == user_id and datos.get('usada', False):
            # Verificar si la licencia es permanente
            if datos.get('expiracion') == 'permanente':
                return True
            
            # Verificar si la licencia no ha expirado
            try:
                expiracion_str = datos.get('expiracion')
                if expiracion_str and expiracion_str != 'permanente':
                    # Asegurar el formato correcto de la fecha
                    if 'T' not in expiracion_str:
                        expiracion_str += 'T00:00:00'
                    expiracion = datetime.fromisoformat(expiracion_str)
                    if datetime.now() < expiracion:
                        return True
            except (ValueError, TypeError) as e:
                print(f"Error al parsear fecha: {e}")
                continue
    
    return False

def obtener_licencias_usuario(user_id):
    """Obtiene todas las licencias de un usuario"""
    user_id = str(user_id)
    licencias = cargar_licencias()
    licencias_usuario = []
    
    for clave, datos in licencias.items():
        if datos.get('usuario') == user_id:
            licencias_usuario.append({
                'clave': clave,
                'expiracion': datos.get('expiracion'),
                'fecha_uso': datos.get('fecha_uso')
            })
    
    return licencias_usuario

def canjear_licencia(clave, user_id):
    """Canjea una licencia y devuelve (éxito, mensaje) - CORREGIDO"""
    user_id = str(user_id)
    licencias = cargar_licencias()
    
    if clave not in licencias:
        return False, "Clave inválida o no existe."
    
    if licencias[clave].get('usada', False):
        return False, "Esta clave ya ha sido utilizada."
    
    expiracion = licencias[clave].get('expiracion')
    if expiracion != 'permanente':
        try:
            if expiracion:
                # Asegurar el formato correcto de la fecha
                if 'T' not in expiracion:
                    expiracion += 'T00:00:00'
                expiracion_dt = datetime.fromisoformat(expiracion)
                if datetime.now() > expiracion_dt:
                    return False, "Esta clave ha expirado."
        except (ValueError, TypeError) as e:
            return False, f"Error en el formato de expiración: {e}"
    
    # Canjear la clave
    licencias[clave]['usada'] = True
    licencias[clave]['usuario'] = user_id
    licencias[clave]['fecha_uso'] = datetime.now().isoformat()
    
    guardar_licencias(licencias)
    
    return True, "Licencia activada correctamente."