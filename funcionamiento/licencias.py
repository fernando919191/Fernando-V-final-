import os
from datetime import datetime

# Ruta al archivo de licencias
LICENCIAS_FILE = os.path.join(os.path.dirname(__file__), '..', 'licencias.txt')

def cargar_licencias():
    """Carga las licencias desde el archivo TXT"""
    licencias = {}
    try:
        with open(LICENCIAS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    clave, datos_str = line.split(':', 1)
                    # Formato: clave:expiracion|usada|usuario|fecha_uso
                    datos_partes = datos_str.split('|')
                    if len(datos_partes) >= 4:
                        licencias[clave] = {
                            'expiracion': datos_partes[0],
                            'usada': datos_partes[1].lower() == 'true',
                            'usuario': datos_partes[2] if datos_partes[2] != 'None' else None,
                            'fecha_uso': datos_partes[3] if datos_partes[3] != 'None' else None
                        }
    except FileNotFoundError:
        # Si el archivo no existe, se creará automáticamente al guardar
        pass
    except Exception as e:
        print(f"Error cargando licencias: {e}")
    return licencias

def guardar_licencias(licencias):
    """Guarda las licencias en el archivo TXT"""
    try:
        with open(LICENCIAS_FILE, 'w', encoding='utf-8') as f:
            for clave, datos in licencias.items():
                # Formato: clave:expiracion|usada|usuario|fecha_uso
                linea = f"{clave}:{datos['expiracion']}|{datos['usada']}|{datos['usuario']}|{datos['fecha_uso']}\n"
                f.write(linea)
        return True
    except Exception as e:
        print(f"Error guardando licencias: {e}")
        return False

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
                    expiracion = datetime.fromisoformat(expiracion_str)
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
        if datos.get('usuario') == user_id:
            tiempo_restante = calcular_tiempo_restante(datos.get('expiracion'))
            licencias_usuario.append({
                'clave': clave,
                'expiracion': datos.get('expiracion'),
                'fecha_uso': datos.get('fecha_uso'),
                'tiempo_restante': tiempo_restante
            })
    
    return licencias_usuario

def canjear_licencia(clave, user_id):
    """Canjea una licencia y devuelve (éxito, mensaje)"""
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
                expiracion_dt = datetime.fromisoformat(expiracion)
                if datetime.now() > expiracion_dt:
                    return False, "Esta clave ha expirado."
        except (ValueError, TypeError):
            return False, "Error en el formato de expiración."
    
    # Canjear la clave
    licencias[clave]['usada'] = True
    licencias[clave]['usuario'] = user_id
    licencias[clave]['fecha_uso'] = datetime.now().isoformat()
    
    # Guardar los cambios
    if guardar_licencias(licencias):
        return True, "Licencia activada correctamente."
    else:
        return False, "Error al guardar la licencia."