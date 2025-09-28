import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.ip_lookup import ip_lookup

logger = logging.getLogger(__name__)

async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ip command for IP address lookup"""
    try:
        # Check if IP address was provided
        if not context.args:
            await update.message.reply_text(
                "❌ *Uso incorrecto*\n\n"
                "• Use: `/ip <dirección-IP>`\n"
                "• Ejemplo: `/ip 200.68.167.143`\n"
                "• Ejemplo: `/ip 189.792.179.1`\n\n"
                "📡 *Formatos soportados:* IPv4 e IPv6",
                parse_mode='Markdown'
            )
            return
        
        ip_address = context.args[0].strip()
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🔍 *Buscando información para IP:* `{ip_address}`\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "⏰ _Consultando base de datos..._",
            parse_mode='Markdown'
        )
        
        # Perform IP lookup
        success, ip_data, message = await ip_lookup.lookup_ip(ip_address)
        
        if not success:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=f"❌ *Error en búsqueda*\n\n{message}\n\n• Verifique la IP e intente nuevamente.",
                parse_mode='Markdown'
            )
            return
        
        # Calculate threat score
        threat_score = ip_lookup.calculate_threat_score(ip_data)
        
        # Format response
        response = ip_lookup.format_response(ip_address, ip_data, threat_score)
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text=response,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error en comando ip: {e}")
        await update.message.reply_text(
            "❌ *Error crítico*\n\n"
            "No se pudo procesar la búsqueda de IP. "
            "Intenta nuevamente o verifica la dirección IP.",
            parse_mode='Markdown'
        )

# Exportar el handler para registro
ip_handler = CommandHandler("ip", ip)