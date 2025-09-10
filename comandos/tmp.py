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

# Configuración CORRECTA de RapidAPI (Privatix Temp Mail)
RAPIDAPI_KEY = "4ec1f5f2d0mshc869b078e5df92fp111bdejsn1bf0d651cb88"
RAPIDAPI_HOST = "privatix-temp-mail-v1.p.rapidapi.com"

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
        
        # 1. Obtener dominios disponibles
        domain = await get_domains(session)
        if not domain:
            await update.message.reply_text("❌ Error al obtener dominios. Intenta nuevamente.")
            return
        
        # 2. Generar correo temporal
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email_address = f"{random_name}@{domain}"
        
        # Guardar información del correo
        user_emails[user_id] = {
            'email': email_address,
            'created_at': datetime.now().strftime("%H:%M:%S"),
            'last_check': datetime.now(),
            'message_count': 0,
            'session': session,
            'hash': random_name  # Guardamos el hash para consultas
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

async def get_domains(session):
    """Obtiene dominios disponibles de la API"""
    try:
        url = "https://privatix-temp-mail-v1.p.rapidapi.com/request/domains/"
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # La API devuelve una lista de dominios, elegimos uno aleatorio
                return random.choice(data) if data else "gmail.com"
            else:
                print(f"Error getting domains: {response.status}")
                return "gmail.com"
                
    except Exception as e:
        print(f"Error getting domains: {e}")
        return "gmail.com"

async def monitor_emails(user_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitorea los correos entrantes usando RapidAPI"""
    
    if user_id not in user_emails:
        return
    
    email_info = user_emails[user_id]
    email_hash = email_info['hash']
    session = email_info['session']
    
    try:
        while user_id in user_emails:
            # Verificar expiración (1 hora)
            created_time = datetime.strptime(email_info['created_at'], "%H:%M:%S")
            if datetime.now() - created_time > timedelta(hours=1):
                await cleanup_user_email(user_id, update, "⏰ El correo temporal ha expirado (1 hora).")
                break
            
            # Verificar nuevos mensajes
            messages = await check_emails(session, email_hash)
            
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

async def check_emails(session, email_hash):
    """Verifica mensajes usando la API correcta"""
    try:
        url = f"https://privatix-temp-mail-v1.p.rapidapi.com/request/mail/id/{email_hash}/"
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            elif response.status == 404:
                # No hay mensajes aún
                return []
            else:
                print(f"API check error: {response.status}")
                return []
                
    except Exception as e:
        print(f"Error checking emails: {e}")
        return []

async def forward_email_to_user(user_id: str, email_data: dict, update: Update):
    """Reenvía un correo al usuario con formato mejorado"""
    try:
        subject = email_data.get('mail_subject', 'Sin asunto')
        sender = email_data.get('mail_from', 'Desconocido')
        timestamp = email_data.get('mail_timestamp', '')
        # Para el contenido, necesitarías hacer otra request para obtener el cuerpo completo
        
        # Formatear el mensaje
        message = (
            f"📨 *NUEVO CORREO RECIBIDO*\n\n"
            f"👤 *De:* {sender}\n"
            f"📋 *Asunto:* {subject}\n"
            f"⏰ *Hora:* {timestamp}\n\n"
            f"📝 *Contenido:*\n"
            f"ℹ️ Usa /tmpread [id] para ver el contenido completo\n\n"
            f"🔗 *Tu correo temporal:* `{user_emails[user_id]['email']}`"
        )
        
        # Guardar el ID del mensaje para poder leerlo después
        message_id = email_data.get('mail_id')
        if message_id:
            user_emails[user_id].setdefault('messages', {})[message_id] = email_data
        
        # Enviar notificación al usuario
        await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        print(f"Error forwarding email: {e}")

async def tmp_read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lee el contenido completo de un mensaje"""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_emails:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Debes especificar el ID del mensaje. Ejemplo: /tmpread 123")
        return
    
    message_id = context.args[0]
    email_info = user_emails[user_id]
    
    if 'messages' not in email_info or message_id not in email_info['messages']:
        await update.message.reply_text("❌ Mensaje no encontrado.")
        return
    
    # Aquí deberías hacer una request a la API para obtener el contenido completo
    # usando: /one_mail/id/{message_id}/
    try:
        session = email_info['session']
        url = f"https://privatix-temp-mail-v1.p.rapidapi.com/request/one_mail/id/{message_id}/"
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                message_content = await response.text()
                await update.message.reply_text(
                    f"📧 *Contenido del mensaje:*\n\n{message_content[:1000]}...",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Error al obtener el contenido del mensaje.")
                
    except Exception as e:
        print(f"Error reading message: {e}")
        await update.message.reply_text("❌ Error al leer el mensaje.")

# Las funciones cleanup_user_email, tmp_callback, tmp_stop, tmp_status se mantienen igual
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
            await query.edit_message_text("❌ No tienes un correo temporal activo.")
    
    elif query.data == "tmp_refresh":
        if user_id in user_emails:
            email_info = user_emails[user_id]
            messages = await check_emails(email_info['session'], email_info['hash'])
            
            if messages and len(messages) > email_info['message_count']:
                new_messages = messages[email_info['message_count']:]
                email_info['message_count'] = len(messages)
                
                for msg in new_messages:
                    await forward_email_to_user(user_id, msg, update)
                await query.edit_message_text("✅ Mensajes actualizados.")
            else:
                await query.edit_message_text("🔄 No hay nuevos mensajes.")
        else:
            await query.edit_message_text("❌ No tienes un correo temporal activo.")

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