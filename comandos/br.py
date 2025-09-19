import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from funcionamiento.usuarios import obtener_info_usuario_completa
from utils.braintree_processor import braintree_processor

logger = logging.getLogger(__name__)

async def br(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /br command for Braintree credit card processing"""
    try:
        user_id = str(update.effective_user.id)
        
        # Check if user is premium
        user_info = obtener_info_usuario_completa(user_id)
        if not user_info or not user_info.get('es_premium', False):
            await update.message.reply_text("❌ Este comando es solo para usuarios premium.")
            return
        
        if not context.args:
            await update.message.reply_text("""
❌ Formato incorrecto. Usa:
/br <cc|mes|ano|cvv>
Ejemplo: /br 5265570075484080|04|2027|108
""")
            return
        
        cc_text = ' '.join(context.args)
        
        # Parse CC data
        cc_data = braintree_processor.parse_cc(cc_text)
        if not cc_data:
            await update.message.reply_text("""
❌ Formato de tarjeta inválido. Usa:
/br <cc|mes|ano|cvv>
Ejemplo: /br 5265570075484080|04|2027|108
""")
            return
        
        # Check CC validity
        validity_result = braintree_processor.check_cc_validity(cc_data)
        if not validity_result[0]:
            await update.message.reply_text(f"❌ {validity_result[1]}")
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text("⏳ Procesando tarjeta en Braintree...")
        
        # Get BIN info and process payment concurrently
        bin_info_task = braintree_processor.get_bin_info(cc_data['cc'])
        payment_task = braintree_processor.simulate_braintree_payment(cc_data)
        
        bin_info, payment_result = await asyncio.gather(
            bin_info_task,
            payment_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(bin_info, Exception):
            logger.error(f"Error getting BIN info: {bin_info}")
            bin_info = None
        
        if isinstance(payment_result, Exception):
            logger.error(f"Error processing payment: {payment_result}")
            payment_result = (False, "❌ Error en el procesamiento")
        
        # Format and send response
        response = braintree_processor.format_response(cc_data, validity_result, bin_info, payment_result)
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text=response
        )
        
    except Exception as e:
        logger.error(f"Error en comando br: {e}")
        await update.message.reply_text("❌ Error al procesar la tarjeta. Intenta nuevamente.")

# Exportar el handler para registro
br_handler = CommandHandler("br", br)