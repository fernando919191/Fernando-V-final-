from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application, CommandHandler, CallbackQueryHandler
import aiohttp
import asyncio
import random
import string
from datetime import datetime, timedelta

# Diccionario para almacenar correos por usuario
user_emails = {}

# API de 1secMail (más confiable)
API_BASE = "https://www.1secmail.com/api/v1/"

async def tmp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera un correo temporal nuevo"""
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name
    
    # Verificar si ya tiene un correo activo
    if user_id in user_emails:
        email_info = user_emails[user_id]
        time_elapsed = datetime.now() - email_info['created_time']
        time_remaining = timedelta(minutes=10) - time_elapsed
        
        if time_remaining.total_seconds() > 0:
            await update.message.reply_text(
                f"📧 Ya tienes un correo temporal activo:\n"
                f"• Correo: `{email_info['email']}`\n"
                f"• Creado: {email_info['created_at']}\n"
                f"• Mensajes: {len(email_info['messages'])} recibidos\n"
                f"• Tiempo restante: {int(time_remaining.total_seconds() // 60)} minutos\n\n"
                f"💡 Usa /tmprefresh para ver nuevos mensajes",
                parse_mode='Markdown'
            )
            return
        else:
            # Eliminar correo expirado
            del user_emails[user_id]
    
    try:
        await update.message.reply_text("🔄 Creando tu correo temporal...")
        
        # Generar correo temporal con 1secMail
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domains = ["1secmail.com", "1secmail.net", "1secmail.org"]
        domain = random.choice(domains)
        email_address = f"{random_name}@{domain}"
        
        # Guardar información del correo
        user_emails[user_id] = {
            'email': email_address,
            'login': random_name,
            'domain': domain,
            'created_at': datetime.now().strftime("%H:%M:%S"),
            'created_time': datetime.now(),
            'messages': [],
            'last_check': datetime.now(),
            'active': True,
            'message_count': 0
        }
        
        # Mensaje con botones CORREGIDOS
        keyboard = [
            [InlineKeyboardButton("🔄 Refrescar", callback_data="refresh")],
            [InlineKeyboardButton("📧 Ver Mensajes", callback_data="view_messages")],
            [InlineKeyboardButton("🛑 Detener", callback_data="stop")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await update.message.reply_text(
            f"✅ *¡Correo temporal creado!*\n\n"
            f"📧 *Correo:* `{email_address}`\n"
            f"👤 *Usuario:* {username}\n"
            f"⏰ *Expira en:* 10 minutos\n\n"
            f"🔍 *Monitoreando nuevos mensajes...*\n"
            f"💡 Usa este correo para registrarte en sitios web\n\n"
            f"📝 Se revisarán automáticamente nuevos mensajes cada 30 segundos",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Guardar ID del mensaje para editar después
        user_emails[user_id]['message_id'] = message.message_id
        
        # Iniciar monitoreo en segundo plano
        asyncio.create_task(monitor_emails(user_id, update, context))
        
    except Exception as e:
        await update.message.reply_text("❌ Error al crear el correo temporal. Intenta nuevamente.")
        print(f"Error en tmp: {e}")

async def monitor_emails(user_id: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitorea los correos entrantes en segundo plano"""
    while user_id in user_emails and user_emails[user_id]['active']:
        try:
            email_info = user_emails[user_id]
            
            # Verificar expiración (10 minutos)
            time_elapsed = datetime.now() - email_info['created_time']
            if time_elapsed > timedelta(minutes=10):
                if user_id in user_emails:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="⏰ El correo temporal ha expirado (10 minutos).")
                    del user_emails[user_id]
                break
            
            # Verificar nuevos mensajes
            new_messages = await check_emails(email_info['login'], email_info['domain'])
            
            if new_messages:
                # Filtrar solo mensajes nuevos
                existing_ids = [msg['id'] for msg in email_info['messages']]
                really_new_messages = [msg for msg in new_messages if msg['id'] not in existing_ids]
                
                if really_new_messages:
                    email_info['messages'].extend(really_new_messages)
                    email_info['message_count'] += len(really_new_messages)
                    
                    for msg in really_new_messages:
                        await notify_new_email(user_id, msg, update, context)
            
            # Esperar 30 segundos entre checks
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Error en monitor_emails: {e}")
            break

async def check_emails(login: str, domain: str):
    """Verifica mensajes usando 1secMail API"""
    try:
        url = f"{API_BASE}?action=getMessages&login={login}&domain={domain}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    messages = await response.json()
                    return messages
                else:
                    return []
                    
    except Exception as e:
        print(f"Error checking emails: {e}")
        return []

async def notify_new_email(user_id: str, email_data: dict, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Notifica sobre un nuevo correo recibido"""
    try:
        email_info = user_emails[user_id]
        message_id = email_data['id']
        
        # Obtener contenido completo del mensaje
        full_message = await get_email_content(email_info['login'], email_info['domain'], message_id)
        
        if full_message:
            subject = full_message.get('subject', 'Sin asunto')
            sender = full_message.get('from', 'Desconocido')
            date = full_message.get('date', '')
            body = full_message.get('textBody', full_message.get('body', 'No content'))
            
            # Acortar el cuerpo si es muy largo
            if body and len(body) > 300:
                body = body[:300] + '...'
            
            # Botones para el mensaje
            keyboard = [
                [InlineKeyboardButton("📖 Leer completo", callback_data=f"read_{message_id}")],
                [InlineKeyboardButton("🗑️ Eliminar", callback_data=f"delete_{message_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = (
                f"📨 *NUEVO CORREO RECIBIDO*\n\n"
                f"👤 *De:* {sender}\n"
                f"📋 *Asunto:* {subject}\n"
                f"⏰ *Fecha:* {date}\n\n"
                f"📝 *Preview:*\n{body}\n\n"
                f"📧 *Tu correo:* `{email_info['email']}`"
            )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
    except Exception as e:
        print(f"Error notifying email: {e}")

async def get_email_content(login: str, domain: str, message_id: int):
    """Obtiene el contenido completo de un mensaje"""
    try:
        url = f"{API_BASE}?action=readMessage&login={login}&domain={domain}&id={message_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
                    
    except Exception as e:
        print(f"Error getting email content: {e}")
        return None

async def tmp_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fuerza la verificación de nuevos mensajes"""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_emails:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")
        return
    
    email_info = user_emails[user_id]
    new_messages = await check_emails(email_info['login'], email_info['domain'])
    
    if new_messages:
        existing_ids = [msg['id'] for msg in email_info['messages']]
        really_new_messages = [msg for msg in new_messages if msg['id'] not in existing_ids]
        
        if really_new_messages:
            email_info['messages'].extend(really_new_messages)
            email_info['message_count'] += len(really_new_messages)
            for msg in really_new_messages:
                await notify_new_email(user_id, msg, update, context)
            await update.message.reply_text(f"✅ {len(really_new_messages)} nuevo(s) mensaje(s)")
        else:
            await update.message.reply_text("🔄 No hay nuevos mensajes.")
    else:
        await update.message.reply_text("📭 No hay mensajes en tu buzón.")

async def tmp_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra todos los mensajes recibidos"""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_emails:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")
        return
    
    email_info = user_emails[user_id]
    
    if not email_info['messages']:
        await update.message.reply_text("📭 No has recibido ningún mensaje aún.")
        return
    
    message_list = "📧 *Tus mensajes recibidos:*\n\n"
    for i, msg in enumerate(email_info['messages'], 1):
        subject = msg.get('subject', 'Sin asunto')
        sender = msg.get('from', 'Desconocido')
        message_list += f"{i}. 🆔 `{msg['id']}` - {subject}\n   👤 De: {sender}\n\n"
    
    message_list += "💡 Usa /tmpread [ID] para leer un mensaje específico"
    await update.message.reply_text(message_list, parse_mode='Markdown')

async def tmp_read(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lee un mensaje específico"""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_emails:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Debes especificar el ID del mensaje. Ejemplo: /tmpread 123")
        return
    
    try:
        message_id = int(context.args[0])
        email_info = user_emails[user_id]
        
        # Buscar el mensaje
        message_data = None
        for msg in email_info['messages']:
            if msg['id'] == message_id:
                message_data = msg
                break
        
        if not message_data:
            await update.message.reply_text("❌ Mensaje no encontrado.")
            return
        
        # Obtener contenido completo
        full_content = await get_email_content(email_info['login'], email_info['domain'], message_id)
        
        if full_content:
            subject = full_content.get('subject', 'Sin asunto')
            sender = full_content.get('from', 'Desconocido')
            date = full_content.get('date', '')
            body = full_content.get('textBody', full_content.get('body', 'No content'))
            
            # Acortar si es muy largo
            if len(body) > 3000:
                body = body[:3000] + "...\n\n📝 *Contenido recortado*"
            
            message_text = (
                f"📧 *MENSAJE COMPLETO*\n\n"
                f"👤 *De:* {sender}\n"
                f"📋 *Asunto:* {subject}\n"
                f"⏰ *Fecha:* {date}\n"
                f"🆔 *ID:* {message_id}\n\n"
                f"📝 *Contenido:*\n{body}"
            )
            
            await update.message.reply_text(message_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Error al obtener el mensaje.")
            
    except ValueError:
        await update.message.reply_text("❌ El ID debe ser un número.")
    except Exception as e:
        await update.message.reply_text("❌ Error al leer el mensaje.")

async def tmp_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detiene el monitoreo del correo"""
    user_id = str(update.effective_user.id)
    
    if user_id in user_emails:
        user_emails[user_id]['active'] = False
        del user_emails[user_id]
        await update.message.reply_text("🛑 Monitoreo detenido. Tu correo temporal ha sido eliminado.")
    else:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")

async def tmp_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado del correo temporal"""
    user_id = str(update.effective_user.id)
    
    if user_id in user_emails:
        email_info = user_emails[user_id]
        time_elapsed = datetime.now() - email_info['created_time']
        time_remaining = timedelta(minutes=10) - time_elapsed
        
        status_text = (
            f"📊 *Estado del correo temporal:*\n\n"
            f"📧 *Correo:* `{email_info['email']}`\n"
            f"⏰ *Creado:* {email_info['created_at']}\n"
            f"📨 *Mensajes:* {len(email_info['messages'])} recibidos\n"
            f"⏱️ *Tiempo restante:* {int(time_remaining.total_seconds() // 60)} minutos\n\n"
            f"📝 *Comandos:*\n"
            f"/tmprefresh - Ver nuevos mensajes\n"
            f"/tmpmessages - Ver todos los mensajes\n"
            f"/tmpread [ID] - Leer mensaje\n"
            f"/tmpstop - Detener monitoreo"
        )
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ No tienes un correo temporal activo.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones - CORREGIDO"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    # Crear un update simulado para los comandos
    fake_update = Update(update.update_id, query)
    
    if data == "refresh":
        await tmp_refresh(fake_update, context)
        
    elif data == "view_messages":
        await tmp_messages(fake_update, context)
        
    elif data == "stop":
        await tmp_stop(fake_update, context)
        
    elif data.startswith("read_"):
        try:
            message_id = data.split("_")[1]
            context.args = [message_id]
            await tmp_read(fake_update, context)
        except Exception as e:
            await query.edit_message_text("❌ Error al leer el mensaje.")
            
    elif data.startswith("delete_"):
        try:
            message_id = int(data.split("_")[1])
            if user_id in user_emails:
                # Eliminar el mensaje de la lista
                user_emails[user_id]['messages'] = [
                    msg for msg in user_emails[user_id]['messages'] 
                    if msg['id'] != message_id
                ]
                await query.edit_message_text("🗑️ Mensaje eliminado de la lista.")
            else:
                await query.edit_message_text("❌ No tienes correo activo.")
        except:
            await query.edit_message_text("❌ Error al eliminar el mensaje.")

# Configuración de handlers
def setup_handlers(application):
    application.add_handler(CommandHandler("tmp", tmp))
    application.add_handler(CommandHandler("tmprefresh", tmp_refresh))
    application.add_handler(CommandHandler("tmpmessages", tmp_messages))
    application.add_handler(CommandHandler("tmpread", tmp_read))
    application.add_handler(CommandHandler("tmpstop", tmp_stop))
    application.add_handler(CommandHandler("tmpstatus", tmp_status))
    application.add_handler(CallbackQueryHandler(handle_callback))