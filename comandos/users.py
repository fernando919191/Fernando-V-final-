import sqlite3
from datetime import datetime
import os
import asyncio

async def get_users_with_licenses(db_path='database.db'):
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
        FROM usuarios u
        LEFT JOIN licencias l ON u.user_id = l.user_id
        ORDER BY u.user_id
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        # Formatear resultados
        resultado = []
        resultado.append(f"{'ID':<15} {'Username':<20} {'Nombre':<25} {'Licencia':<10} {'Expiración':<12} {'Estado':<10}")
        resultado.append("-" * 95)
        
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
            
            # Determinar estado real
            if licencia == 'ACTIVA':
                if vigencia == 'EXPIRADA':
                    estado_display = 'EXPIRADA'
                    licencia_color = 'INACTIVA'
                else:
                    estado_display = 'VIGENTE'
                    licencia_color = 'ACTIVA'
            else:
                estado_display = 'N/A'
                licencia_color = 'INACTIVA'
            
            resultado.append(f"{user_id:<15} {username_display:<20} {nombre_completo:<25} {licencia_color:<10} {expiracion_display:<12} {estado_display:<10}")
        
        resultado.append(f"\nTotal de usuarios: {len(users)}")
        return "\n".join(resultado)
        
    except sqlite3.Error as e:
        return f"Error de base de datos: {e}"
    except Exception as e:
        return f"Error inesperado: {e}"
    finally:
        if conn:
            conn.close()

async def users(update, context):
    """Función de comando asíncrona para el bot."""
    db_path = 'hellobot.db' if os.path.exists('hellobot.db') else 'database.db'
    
    # Enviar mensaje de "procesando"
    processing_msg = await update.message.reply_text("📊 Obteniendo información de usuarios...")
    
    try:
        # Obtener los datos
        resultado = await get_users_with_licenses(db_path)
        
        # Telegram tiene límite de 4096 caracteres por mensaje
        if len(resultado) > 4000:
            # Dividir en partes si es muy largo
            parts = [resultado[i:i+4000] for i in range(0, len(resultado), 4000)]
            for part in parts:
                await update.message.reply_text(f"```\n{part}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"```\n{resultado}\n```", parse_mode='Markdown')
            
    except Exception as e:
        error_msg = f"❌ Error al obtener usuarios: {str(e)}"
        await update.message.reply_text(error_msg)
    finally:
        # Eliminar mensaje de "procesando"
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_msg.message_id)
        except:
            pass  # Si no se puede eliminar, no pasa nada

# Función para uso standalone (desde consola)
async def main_standalone():
    """Función principal para uso desde consola"""
    if os.path.exists('hellobot.db'):
        print("Usando hellobot.db...")
        resultado = await get_users_with_licenses('hellobot.db')
    elif os.path.exists('database.db'):
        print("Usando database.db...")
        resultado = await get_users_with_licenses('database.db')
    else:
        print("No se encontró ninguna base de datos (.db) en el directorio actual")
        return
    
    print(resultado)

if __name__ == "__main__":
    # Ejecutar versión standalone
    asyncio.run(main_standalone())