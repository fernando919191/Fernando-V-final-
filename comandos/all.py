import logging
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_todos_usuarios
from index import es_administrador

logger = logging.getLogger(__name__)

async def all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if not es_administrador(user_id, username):
            await update.message.reply_text("❌ Solo administradores pueden usar este comando.")
            return
        
        usuarios = obtener_todos_usuarios()
        
        if not usuarios:
            await update.message.reply_text("📭 No hay usuarios registrados.")
            return
        
        # Menciones con manejo robusto de errores
        menciones = []
        usuarios_con_error = []
        
        for usuario in usuarios:
            try:
                user_id_str = str(usuario.get('user_id', ''))
                username_real = str(usuario.get('username', '')).strip()
                
                # Validaciones estrictas
                if (username_real and 
                    len(username_real) > 1 and 
                    username_real.lower() not in ['usuario', 'none', 'null', ''] and
                    not username_real.isspace()):
                    
                    menciones.append(f"@{username_real}")
                    
            except Exception as e:
                usuarios_con_error.append(usuario.get('user_id', 'desconocido'))
                logger.warning(f"Usuario con error en mención: {usuario.get('user_id')} - {e}")
                continue
        
        if not menciones:
            await update.message.reply_text("ℹ️ No hay usuarios con username válido para mencionar.")
            return
        
        # Enviar menciones en partes si son muchas
        mensaje_completo = " ".join(menciones)
        
        # Dividir si el mensaje es muy largo
        if len(mensaje_completo) > 4000:
            partes = []
            parte_actual = ""
            
            for mencion in menciones:
                if len(parte_actual) + len(mencion) + 1 > 4000:
                    partes.append(parte_actual.strip())
                    parte_actual = mencion
                else:
                    parte_actual += " " + mencion
            
            if parte_actual:
                partes.append(parte_actual.strip())
            
            # Enviar cada parte
            for i, parte in enumerate(partes, 1):
                await update.message.reply_text(
                    f"📢 **Mención global** (Parte {i}/{len(partes)})\n\n{parte}",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                f"📢 **Mención global**\n\n{mensaje_completo}",
                parse_mode='Markdown'
            )
        
        # Log para debugging
        logger.info(f"Comando /all ejecutado por {user_id}. {len(menciones)} menciones, {len(usuarios_con_error)} errores")
        
    except Exception as e:
        logger.error(f"Error crítico en comando all: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al procesar el comando. Revisa logs.")