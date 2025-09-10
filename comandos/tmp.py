from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import aiohttp
import asyncio
import random
import string
from datetime import datetime, timedelta

# Diccionario para almacenar correos por usuario
user_emails = {}
user_sessions = {}

# Configuración de RapidAPI
RAPIDAPI_KEY = "4ec1f5f2d0mshc869b078e5df92fp111bdejsn1bf0d651cb88"
RAPIDAPI_HOST = "temp-mail44.p.rapidapi.com"

async def tmp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera un correo temporal usando RapidAPI"""
    
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name
    
    # Verificar si ya tiene un correo activo
    if user_id in user_emails:
        email_info = user_emails[user_id]
        await update.message.reply_text(
            f"📧 Ya tienes un correo temporal activo:\n"
            f"• Correo: `{email_info['email']}`\n"
            f"• Creado: {email_info['created_at']}\n"
            f"• Mensajes: {email_info['message_count']} recibidos\n\n"
            f"ℹ️ Los correos se eliminan automáticamente después de 1 hora.",
            parse_mode='Markdown'
        )
        return
    
    try:
        await update.message.reply_text("🔄 Creando tu correo temporal...")
        
        # Crear sesión para el usuario con headers de RapidAPI
        session = aiohttp.ClientSession()
        user_sessions[user_id] = session
        
        # 1. Crear correo temporal con RapidAPI
        email_address = await create_temp_email_rapidapi(session)
        
        if not email_address:
            # Fallback: generar correo aleatorio
            email_address = await create_fallback_email()
        
        # Guardar información del correo
        user_emails[user_id] = {
            'email': email_address,
            'created_at': datetime.now().strftime("%H:%M:%S"),
            'last_check': datetime.now(),
            'message_count': 0,
            'session': session
        }
        
        # Mensaje con botones
        keyboard = [
            [InlineKeyboardButton("📧 Refrescar", callback_data="tmp_refresh")],
            [InlineKeyboardButton("🛑 Detener", callback_data="tmp_stop")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📧 ¡Correo temporal creado!\n\n"
            f"• Correo: `{email_address}`\n"
            f"• Usuario: {username}\n\n"
            f"⚠️ Este correo expirará en 1 hora\n"
            f"🔍 Monitoreando nuevos mensajes...\n\n"
            f"💡 Usa este correo para registrarte en sitios web",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Iniciar monitoreo de correos
        asyncio.create_task(monitor_emails(user_id, update, context))
        
    except Exception as e:
        await update.message.reply_text("❌ Error al crear el correo temporal. Intenta nuevamente.")
        print(f"Error en tmp: {e}")

async def create_temp_email_rapidapi(session):
    """Crea un correo temporal usando RapidAPI"""
    try:
        url = "https://temp-mail44.p.rapidapi.com/api/v3/email/new"
        
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
        
        # Generar nombre aleatorio para el correo
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        payload = {"name": random_name}
        
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('email')
            else:
                print(f"RapidAPI error: {response.status}")
                return None
                
    except Exception as e:
        print(f"Error creating email with RapidAPI: {e}")
        return None

async def create_fallback_email():
    """Genera un correo de respaldo si RapidAPI falla"""
    random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domains = [
        'gmail.com', 'yahoo.com', 'outlook.com', 
        'knilok.com', 'finews.biz', 'fexpost.com'
    ]
    return f"{random_name}@{random.choice(domains)}"

async def monitor_emails(user_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitorea los correos entrantes usando RapidAPI"""
    
    if user_id not in user_emails:
        return
    
    email_info = user_emails[user_id]
    email_address = email_info['email']
    session = email_info['session']
    
    try:
        while user_id in user_emails:
            # Verificar expiración (1 hora)
            created_time = datetime.strptime(email_info['created_at'], "%H:%M:%S")
            if datetime.now() - created_time > timedelta(hours=1):
                await cleanup_user_email(user_id, update, "⏰ El correo temporal ha expirado (1 hora).")
                break
            
            # Verificar nuevos mensajes con RapidAPI
            messages = await check_emails_rapidapi(session, email_address)
            
            if messages and len(messages) > email_info['message_count']:
                new_messages = messages[email_info['message_count']:]
                email_info['message_count'] = len(messages)
                
                for msg in new_messages:
                    await forward_email_to_user(user_id, msg, update)
            
            # Esperar 20 segundos entre checks
            await asyncio.sleep(20)
            
    except Exception as e:
        print(f"Error en monitor_emails para {user_id}: {e}")
        await cleanup_user_email(user_id, update, "❌ Error en el monitoreo del correo.")

async def check_emails_rapidapi(session, email_address):
    """Verifica mensajes usando RapidAPI"""
    try:
        # Extraer el nombre del correo (antes del @)
        mailbox_name = email_address.split('@')[0]
        
        url = f"https://temp-mail44.p.rapidapi.com/api/v3/email/{mailbox_name}/messages"
        
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                print(f"RapidAPI check error: {response.status}")
                return []
                
    except Exception as e:
        print(f"Error checking emails with RapidAPI: {e}")
        return []

async def forward_email_to_user(user_id: str, email_data: dict, update: Update):
    """Reenvía un correo al usuario con formato mejorado"""
    try:
        subject = email_data.get('subject', 'Sin asunto')
        sender = email_data.get('from', 'Desconocido')
        sender_name = email_data.get('from_name', sender)
        timestamp = email_data.get('created_at', '')
        body = email_data.get('body', '')[:200] + '...' if email_data.get('body') else 'No content available'
        
        # Formatear el mensaje
        message = (
            f"📨 *NUEVO CORREO RECIBIDO*\n\n"
            f"👤 *De:* {sender_name}\n"
            f"📧 *Dirección:* {sender}\n"
            f"📋 *Asunto:* {subject}\n"
            f"⏰ *Hora:* {timestamp}\n\n"
            f"📝 *Contenido:*\n{body}\n\n"
            f"🔗 *Tu correo temporal:* `{user_emails[user_id]['email']}`"
        )
        
        # Enviar notificación al usuario
        await update.message.reply_text(message, parse_mode='Markdown')
            
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

async def tmp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if query.data == "tmp_stop":
        if user_id in user_emails:
            await cleanup_user_email(user_id, update, "🛑 Monitoreo de correo detenido.")
        else:
            await query.message.reply_text("❌ No tienes un correo temporal activo.")
    
    elif query.data == "tmp_refresh":
        if user_id in user_emails:
            # Forzar verificación inmediata
            email_info = user_emails[user_id]
            messages = await check_emails_rapidapi(email_info['session'], email_info['email'])
            
            if messages and len(messages) > email_info['message_count']:
                new_messages = messages[email_info['message_count']:]
                email_info['message_count'] = len(messages)
                
                for msg in new_messages:
                    await forward_email_to_user(user_id, msg, update)
            else:
                await query.message.reply_text("🔄 No hay nuevos mensajes.")
        else:
            await query.message.reply_text("❌ No tienes un correo temporal activo.")

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
            f"📊 *Estado de tu correo temporal:*\n\n"
            f"• *Correo:* `{email_info['email']}`\n"
            f"• *Creado:* {email_info['created_at']}\n"
            f"• *Mensajes recibidos:* {email_info['message_count']}\n"
            f"• *Tiempo restante:* {time_remaining.seconds//60} minutos\n\n"
            f"Usa /tmpstop para detener el monitoreo.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")