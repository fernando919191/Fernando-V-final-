import sqlite3
from datetime import datetime

def get_users_with_licenses(db_path='database.db'):
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Consulta para obtener usuarios con estado de licencia
        query = """
        SELECT 
            u.user_id, 
            u.username, 
            u.first_name, 
            u.last_name,
            CASE 
                WHEN l.activa = 1 THEN 'ACTIVA' 
                ELSE 'INACTIVA' 
            END as estado_licencia,
            l.fecha_expiracion,
            CASE
                WHEN l.activa = 1 AND l.fecha_expiracion < date('now') THEN 'EXPIRADA'
                ELSE 'VIGENTE'
            END as vigencia
        FROM usuaries u
        LEFT JOIN licencias l ON u.user_id = l.user_id
        ORDER BY u.user_id
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        # Mostrar resultados
        print(f"\n{'ID':<15} {'Username':<20} {'Nombre':<25} {'Licencia':<10} {'Expiración':<12} {'Estado':<10}")
        print("-" * 95)
        
        for user in users:
            user_id, username, first_name, last_name, licencia, expiracion, vigencia = user
            
            # Formatear nombre completo
            nombre_completo = f"{first_name or ''} {last_name or ''}".strip()
            if not nombre_completo:
                nombre_completo = "Sin nombre"
            
            # Formatear username
            username_display = f"@{username}" if username else "Sin username"
            
            # Formatear fecha de expiración
            expiracion_display = expiracion or "N/A"
            
            # Determinar color de estado (solo para consola)
            if licencia == 'ACTIVA':
                if vigencia == 'EXPIRADA':
                    estado_display = 'EXPIRADA'
                    licencia_color = 'INACTIVA'  # Aunque diga ACTIVA, está expirada
                else:
                    estado_display = 'VIGENTE'
                    licencia_color = 'ACTIVA'
            else:
                estado_display = 'N/A'
                licencia_color = 'INACTIVA'
            
            print(f"{user_id:<15} {username_display:<20} {nombre_completo:<25} {licencia_color:<10} {expiracion_display:<12} {estado_display:<10}")
        
        print(f"\nTotal de usuarios: {len(users)}")
        
    except sqlite3.Error as e:
        print(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Verificar qué base de datos existe
    import os
    if os.path.exists('hellobot.db'):
        print("Usando hellobot.db...")
        get_users_with_licenses('hellobot.db')
    elif os.path.exists('database.db'):
        print("Usando database.db...")
        get_users_with_licenses('database.db')
    else:
        print("No se encontró ninguna base de datos (.db) en el directorio actual")
