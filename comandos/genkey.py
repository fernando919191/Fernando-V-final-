# comandos/genkey.py
import logging
import secrets
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.licencias import guardar_key_en_db
from index import es_administrador

logger = logging.getLogger(__name__)

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para administradores: generar keys de licencia"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        # Verificar si es administrador
        if not es_administrador(user_id, username):
            await update.message.reply_text("❌ Solo los administradores pueden generar keys.")
            return
        
        # Parsear argumentos
        args = context.args
        tipo = "30d"  # Por defecto 30 días
        cantidad = 1  # Por defecto 1 key
        
        if args:
            # Verificar tipo de key
            if args[0].lower() in ['30d', '30days', '30']:
                tipo = "30d"
                dias = 30
            elif args[0].lower() in ['perm', 'permanent', 'forever']:
                tipo = "perm"
                dias = 9999  # Licencia permanente
            elif args[0].lower() in ['7d', '7days', '7']:
                tipo = "7d"
                dias = 7
            elif args[0].lower() in ['90d', '90days', '90']:
                tipo = "90d"
                dias = 90
            else:
                # Si el primer argumento es número, es la cantidad
                if args[0].isdigit():
                    cantidad = max(1, min(100, int(args[0])))
                else:
                    await update.message.reply_text(
                        "📝 Uso: `.genkey [tipo] [cantidad]`\n\n"
                        "Tipos disponibles:\n"
                        "• `30d` - 30 días (por defecto)\n"
                        "• `perm` - Permanente\n"
                        "• `7d` - 7 días\n"
                        "• `90d` - 90 días\n\n"
                        "Ejemplos:\n"
                        "• `.genkey` - 1 key de 30 días\n"
                        "• `.genkey perm 5` - 5 keys permanentes\n"
                        "• `.genkey 10` - 10 keys de 30 días\n"
                        "• `.genkey 7d 3` - 3 keys de 7 días",
                        parse_mode="Markdown"
                    )
                    return
            
            # Verificar si hay segundo argumento para cantidad
            if len(args) > 1 and args[1].isdigit():
                cantidad = max(1, min(100, int(args[1])))
            elif len(args) == 1 and args[0].isdigit():
                # Solo se pasó un número (cantidad)
                cantidad = max(1, min(100, int(args[0])))
                tipo = "30d"
                dias = 30
        else:
            dias = 30  # Valor por defecto
        
        # Generar keys
        keys_generadas = []
        for i in range(cantidad):
            key = secrets.token_hex(8).upper()  # Key de 16 caracteres
            exito = guardar_key_en_db(key, dias, tipo)
            
            if exito:
                keys_generadas.append(key)
            else:
                logger.error(f"Error guardando key: {key}")
        
        if not keys_generadas:
            await update.message.reply_text("❌ Error al generar las keys.")
            return
        
        # Formatear respuesta
        tipo_texto = {
            "30d": "30 días",
            "perm": "PERMANENTE", 
            "7d": "7 días",
            "90d": "90 días"
        }.get(tipo, f"{dias} días")
        
        respuesta = (
            f"✅ *Keys generadas exitosamente*\n\n"
            f"📋 **Tipo:** {tipo_texto}\n"
            f"🔢 **Cantidad:** {len(keys_generadas)}\n\n"
            f"🔑 **Keys:**\n"
        )
        
        # Agregar keys a la respuesta
        for i, key in enumerate(keys_generadas, 1):
            respuesta += f"`{i}. {key}`\n"
        
        respuesta += (
            f"\n📝 **Para canjear:**\n"
            f"Usa `/key <key>` o `.key <key>`\n\n"
            f"⏰ **Validez:** {tipo_texto}"
        )
        
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        
        # También enviar por privado al admin para mayor seguridad
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📦 **Keys generadas - Backup**\n\n"
                     f"Tipo: {tipo_texto}\n"
                     f"Cantidad: {len(keys_generadas)}\n\n"
                     f"{chr(10).join(keys_generadas)}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"No se pudo enviar backup al admin: {e}")
            
    except Exception as e:
        logger.error(f"Error en comando genkey: {e}", exc_info=True)
        await update.message.reply_text("❌ Error al generar keys. Verifica la sintaxis.")