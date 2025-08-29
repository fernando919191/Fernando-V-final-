import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hellbot.db')

def get_connection():
    """Obtiene conexión a SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder a las columnas por nombre
    return conn

def init_database():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de licencias
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS licencias (
        clave TEXT PRIMARY KEY,
        expiracion TEXT,
        usada BOOLEAN DEFAULT FALSE,
        usuario TEXT,
        fecha_uso TEXT
    )
    ''')
    
    # Tabla de usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        fecha_registro TEXT,
        tiene_licencia BOOLEAN DEFAULT FALSE,
        ultima_verificacion TEXT
    )
    ''')
    
    # Tabla de administradores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS administradores (
        user_id TEXT PRIMARY KEY
    )
    ''')
    
    # Insertar admin principal si no existe
    cursor.execute('''
    INSERT OR IGNORE INTO administradores (user_id) VALUES ('6751216122')
    ''')
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al importar
init_database()