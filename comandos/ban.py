import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.error import BadRequest
from index import es_administrador

logger = logging.getLogger(__name__)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando .ban para banear usuarios (solo administradores)"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Verificar si el usuario es administrador
    if not await es_administrador(user.id, user.username):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Verificar que el comando se use en un grupo
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Este comando solo funciona en grupos.")
        return
    
    # Verificar que se mencione a un usuario
    if not update.message.reply_to_message and not context.args:
        await update.message.reply_text(
            "🔨 *Uso del comando .ban:*\n\n"
            "• Responde a un mensaje con `.ban`\n"
            "• O usa `.ban @usuario`\n"
            "• O usa `.ban 123456789` (ID de usuario)\n\n"
            "📌 *Ejemplos:*\n"
            "• Responde a un mensaje spam con `.ban`\n"
            "• `.ban @spammer`\n"
            "• `.ban 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user = None
        reason = "Sin razón especificada"
        
        # Caso 1: Respuesta a un mensaje
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            # Extraer razón de los argumentos si existen
            if context.args:
                reason = ' '.join(context.args)
        
        # Caso 2: Mención por username
        elif context.args and context.args[0].startswith('@'):
            username = context.args[0][1:]
            # Buscar el usuario por username (esto requiere que el bot haya visto al usuario antes)
            try:
                # Intentar obtener el ID del usuario de la base de datos o contexto
                # Por ahora, usaremos un approach más simple
                await update.message.reply_text(
                    f"⚠️ Para banear por username (@{username}), responde a un mensaje de ese usuario."
                )
                return
            except:
                await update.message.reply_text("❌ No se pudo encontrar el usuario mencionado.")
                return
        
        # Caso 3: Mención por ID
        elif context.args and context.args[0].isdigit():
            user_id = int(context.args[0])
            try:
                # Intentar banear por ID
                await chat.ban_member(user_id)
                await update.message.reply_text(f"✅ Usuario con ID {user_id} baneado exitosamente.")
                return
            except BadRequest as e:
                await update.message.reply_text(f"❌ Error al banear: {e.message}")
                return
        
        if not target_user:
            await update.message.reply_text("❌ No se pudo identificar al usuario a banear.")
            return
        
        # Verificar que no sea un administrador
        if await es_administrador(target_user.id, target_user.username):
            await update.message.reply_text("❌ No puedes banear a otro administrador.")
            return
        
        # Banear al usuario
        await chat.ban_member(target_user.id)
        
        # Mensaje de confirmación
        ban_message = (
            f"🔨 *Usuario baneado*\n\n"
            f"👤 *Usuario:* {target_user.mention_markdown()}\n"
            f"🆔 *ID:* `{target_user.id}`\n"
            f"📝 *Razón:* {reason}\n"
            f"👮 *Moderador:* {user.mention_markdown()}\n\n"
            f"✅ *Baneo ejecutado exitosamente*"
        )
        
        await update.message.reply_text(ban_message, parse_mode="Markdown")
        
    except BadRequest as e:
        if "not enough rights" in str(e).lower():
            await update.message.reply_text("❌ No tengo permisos para banear usuarios en este grupo.")
        elif "user is an administrator" in str(e).lower():
            await update.message.reply_text("❌ No puedo banear a un administrador.")
        else:
            await update.message.reply_text(f"❌ Error al banear: {e.message}")
    
    except Exception as e:
        logger.error(f"Error en comando ban: {e}")
        await update.message.reply_text("❌ Error interno al procesar el comando.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando .unban para desbanear usuarios (solo administradores)"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Verificar si el usuario es administrador
    if not await es_administrador(user.id, user.username):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Verificar que el comando se use en un grupo
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Este comando solo funciona en grupos.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔓 *Uso del comando .unban:*\n\n"
            "• `.unban @usuario`\n"
            "• `.unban 123456789` (ID de usuario)\n\n"
            "📌 *Ejemplo:*\n"
            "• `.unban @usuario`\n"
            "• `.unban 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_id = None
        
        # Caso 1: Mención por username (necesitamos el ID)
        if context.args[0].startswith('@'):
            username = context.args[0][1:]
            # En un implementation real, necesitarías una base de datos de usuarios baneados
            await update.message.reply_text(
                "⚠️ Para desbanear por username, necesito el ID del usuario. "
                "Usa `.unban ID_USUARIO` donde ID_USUARIO es el número de ID."
            )
            return
        
        # Caso 2: Mención por ID
        elif context.args[0].isdigit():
            target_id = int(context.args[0])
        
        if not target_id:
            await update.message.reply_text("❌ ID de usuario inválido.")
            return
        
        # Desbanear al usuario
        await chat.unban_member(target_id)
        await update.message.reply_text(f"✅ Usuario con ID {target_id} desbaneado exitosamente.")
        
    except BadRequest as e:
        if "not enough rights" in str(e).lower():
            await update.message.reply_text("❌ No tengo permisos para desbanear usuarios en este grupo.")
        else:
            await update.message.reply_text(f"❌ Error al desbanear: {e.message}")
    
    except Exception as e:
        logger.error(f"Error en comando unban: {e}")
        await update.message.reply_text("❌ Error interno al procesar el comando.")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando .kick para expulsar usuarios (solo administradores)"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Verificar si el usuario es administrador
    if not await es_administrador(user.id, user.username):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Verificar que el comando se use en un grupo
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Este comando solo funciona en grupos.")
        return
    
    # Verificar que se mencione a un usuario
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "👢 *Uso del comando .kick:*\n\n"
            "• Responde a un mensaje con `.kick`\n"
            "• O usa `.kick @usuario`\n\n"
            "📌 *Ejemplo:*\n"
            "• Responde a un mensaje con `.kick`\n"
            "• `.kick @spammer`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user = update.message.reply_to_message.from_user
        reason = "Sin razón especificada"
        
        # Extraer razón de los argumentos si existen
        if context.args:
            reason = ' '.join(context.args)
        
        # Verificar que no sea un administrador
        if await es_administrador(target_user.id, target_user.username):
            await update.message.reply_text("❌ No puedes expulsar a otro administrador.")
            return
        
        # Expulsar al usuario
        await chat.ban_member(target_user.id)
        await chat.unban_member(target_user.id)  # Unban immediately to make it a kick
        
        # Mensaje de confirmación
        kick_message = (
            f"👢 *Usuario expulsado*\n\n"
            f"👤 *Usuario:* {target_user.mention_markdown()}\n"
            f"🆔 *ID:* `{target_user.id}`\n"
            f"📝 *Razón:* {reason}\n"
            f"👮 *Moderador:* {user.mention_markdown()}\n\n"
            f"✅ *Expulsión ejecutada exitosamente*"
        )
        
        await update.message.reply_text(kick_message, parse_mode="Markdown")
        
    except BadRequest as e:
        if "not enough rights" in str(e).lower():
            await update.message.reply_text("❌ No tengo permisos para expulsar usuarios en este grupo.")
        elif "user is an administrator" in str(e).lower():
            await update.message.reply_text("❌ No puedo expulsar a un administrador.")
        else:
            await update.message.reply_text(f"❌ Error al expulsar: {e.message}")
    
    except Exception as e:
        logger.error(f"Error en comando kick: {e}")
        await update.message.reply_text("❌ Error interno al procesar el comando.")

def setup(application):
    """Configura los handlers para los comandos de moderación"""
    # Agregar handlers para los comandos
    application.add_handler(MessageHandler(filters.Regex(r'^\.ban\b'), ban_command))
    application.add_handler(MessageHandler(filters.Regex(r'^\.unban\b'), unban_command))
    application.add_handler(MessageHandler(filters.Regex(r'^\.kick\b'), kick_command))
    
    # También agregar como CommandHandler por si acaso
    application.add_handler(CommandHandler('ban', ban_command))
    application.add_handler(CommandHandler('unban', unban_command))
    application.add_handler(CommandHandler('kick', kick_command))