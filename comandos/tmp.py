from telegram import Update
from telegram.ext import ContextTypes
import aiohttp
import asyncio
import json
import random
import string
from datetime import datetime, timedelta

# Diccionario para almacenar correos por usuario
user_emails = {}
user_sessions = {}

async def tmp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera un correo temporal único para cada usuario"""
    
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name
    
    # Verificar si ya tiene un correo activo
    if user_id in user_emails:
        email_info = user_emails[user_id]
        await update.message.reply_text(
            f"📧 Ya tienes un correo temporal activo:\n"
            f"• Correo: `{email_info['email']}`\n"
            f"• Creado: {email_info['created_at']}\n\n"
            f"ℹ️ Los correos se eliminan automáticamente después de 1 hora.",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Crear sesión y correo temporal
        await update.message.reply_text("🔄 Creando tu correo temporal...")
        
        # Generar nombre de usuario aleatorio
        random_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        domain = "temp-mail.org"  # Dominio de temp-mail
        
        email_address = f"{random_username}@{domain}"
        
        # Crear sesión para el usuario
        session = aiohttp.ClientSession()
        user_sessions[user_id] = session
        
        # Guardar información del correo
        user_emails[user_id] = {
            'email': email_address,
            'created_at': datetime.now().strftime("%H:%M:%S"),
            'last_check': datetime.now(),
            'message_count': 0
        }
        
        await update.message.reply_text(
            f"📧 ¡Correo temporal creado!\n\n"
            f"• Correo: `{email_address}`\n"
            f"• Usuario: {username}\n\n"
            f"⚠️ Este correo expirará en 1 hora\n"
            f"🔍 Monitoreando nuevos mensajes...",
            parse_mode='Markdown'
        )
        
        # Iniciar monitoreo de correos para este usuario
        asyncio.create_task(monitor_emails(user_id, update, context))
        
    except Exception as e:
        await update.message.reply_text("❌ Error al crear el correo temporal. Intenta nuevamente.")
        print(f"Error en tmp: {e}")

async def monitor_emails(user_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitorea los correos entrantes para un usuario específico"""
    
    if user_id not in user_emails:
        return
    
    email_info = user_emails[user_id]
    email_address = email_info['email']
    
    try:
        while user_id in user_emails:
            # Verificar si el correo ha expirado (1 hora)
            created_time = datetime.strptime(email_info['created_at'], "%H:%M:%S")
            if datetime.now() - created_time > timedelta(hours=1):
                await cleanup_user_email(user_id, update, "⏰ El correo temporal ha expirado (1 hora).")
                break
            
            # Intentar obtener mensajes usando la API de temp-mail
            messages = await check_temp_mail(email_address)
            
            if messages and len(messages) > email_info['message_count']:
                new_messages = messages[email_info['message_count']:]
                email_info['message_count'] = len(messages)
                
                for msg in new_messages:
                    await forward_email_to_user(user_id, msg, update)
            
            # Esperar 30 segundos entre checks
            await asyncio.sleep(30)
            
    except Exception as e:
        print(f"Error en monitor_emails para {user_id}: {e}")
        await cleanup_user_email(user_id, update, "❌ Error en el monitoreo del correo.")

async def check_temp_mail(email: str):
    """Verifica los mensajes del correo temporal usando temp-mail.org"""
    try:
        # Temp-mail.org API endpoint
        url = f"https://web2.temp-mail.org/mailbox/{email}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('messages', [])
                else:
                    return []
                    
    except Exception as e:
        print(f"Error checking temp mail: {e}")
        return []

async def forward_email_to_user(user_id: str, email_data: dict, update: Update):
    """Reenvía un correo al usuario"""
    try:
        subject = email_data.get('subject', 'Sin asunto')
        sender = email_data.get('from', 'Desconocido')
        timestamp = email_data.get('created_at', '')
        
        message = (
            f"📨 Nuevo correo recibido:\n\n"
            f"• De: {sender}\n"
            f"• Asunto: {subject}\n"
            f"• Hora: {timestamp}\n\n"
            f"📧 Contenido disponible en tu correo temporal"
        )
        
        # Enviar notificación al usuario
        if user_id in user_emails:
            await update.message.reply_text(message)
            
    except Exception as e:
        print(f"Error forwarding email: {e}")

async def cleanup_user_email(user_id: str, update: Update, message: str = ""):
    """Limpia los recursos de un usuario"""
    try:
        if user_id in user_sessions:
            session = user_sessions[user_id]
            await session.close()
            del user_sessions[user_id]
        
        if user_id in user_emails:
            del user_emails[user_id]
            
        if message:
            await update.message.reply_text(message)
            
    except Exception as e:
        print(f"Error cleaning up: {e}")

async def tmp_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detiene el monitoreo del correo temporal"""
    user_id = str(update.effective_user.id)
    
    if user_id in user_emails:
        await cleanup_user_email(user_id, update, "🛑 Monitoreo de correo detenido.")
    else:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")

async def tmp_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado del correo temporal"""
    user_id = str(update.effective_user.id)
    
    if user_id in user_emails:
        email_info = user_emails[user_id]
        created_time = datetime.strptime(email_info['created_at'], "%H:%M:%S")
        time_elapsed = datetime.now() - created_time
        time_remaining = timedelta(hours=1) - time_elapsed
        
        await update.message.reply_text(
            f"📊 Estado de tu correo temporal:\n\n"
            f"• Correo: `{email_info['email']}`\n"
            f"• Creado: {email_info['created_at']}\n"
            f"• Mensajes recibidos: {email_info['message_count']}\n"
            f"• Tiempo restante: {time_remaining.seconds//60} minutos\n\n"
            f"Usa /tmpstop para detener el monitoreo.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")