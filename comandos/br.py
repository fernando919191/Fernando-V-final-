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
❌ *Formato incorrecto*. Usa:
/br <cc|mes|ano|cvv>

*Ejemplo:* 
`/br 5265577028194567|09|2029|835`
`/br 5265577028194567/09/2029/835`
`/br 5265577028194567 09 2029 835`
""", parse_mode='Markdown')
            return
        
        cc_text = ' '.join(context.args)
        
        # Parse CC data
        cc_data = braintree_processor.parse_cc(cc_text)
        if not cc_data:
            await update.message.reply_text("""
❌ *Formato de tarjeta inválido*. Usa:

`/br 5265577028194567|09|2029|835`
`/br 5265577028194567/09/2029/835`  
`/br 5265577028194567 09 2029 835`

*Formatos aceptados:* 
• `CC|MM|YYYY|CVV`
• `CC/MM/YYYY/CVV`
• `CC MM YYYY CVV`
""", parse_mode='Markdown')
            return
        
        # Check CC validity
        validity_result = braintree_processor.check_cc_validity(cc_data)
        if not validity_result[0]:
            await update.message.reply_text(f"❌ *Error de validación:*\n{validity_result[1]}", parse_mode='Markdown')
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 *Procesando tarjeta en Braintree...*", parse_mode='Markdown')
        
        try:
            # Get BIN info and process payment concurrently with timeout
            bin_info_task = braintree_processor.get_bin_info(cc_data['cc'])
            payment_task = braintree_processor.simulate_braintree_payment(cc_data)
            
            # Esperar máximo 10 segundos para ambas tareas
            done, pending = await asyncio.wait(
                [bin_info_task, payment_task],
                timeout=10,
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Cancelar tareas pendientes si timeout
            for task in pending:
                task.cancel()
            
            # Obtener resultados
            bin_info = None
            payment_result = (False, "❌ Timeout en procesamiento", "timeout")
            
            for task in done:
                try:
                    result = task.result()
                    if isinstance(result, dict):  # bin_info
                        bin_info = result
                    else:  # payment_result
                        payment_result = result
                except asyncio.TimeoutError:
                    payment_result = (False, "❌ Timeout en procesamiento", "timeout")
                except Exception as e:
                    logger.error(f"Error en tarea: {e}")
                    payment_result = (False, "❌ Error interno en procesamiento", "internal_error")
            
            # Format and send response
            response = braintree_processor.format_response(cc_data, validity_result, bin_info, payment_result)
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=response,
                parse_mode='Markdown'
            )
            
        except asyncio.TimeoutError:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text="❌ *Timeout:* El procesamiento tardó demasiado. Intenta nuevamente.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error en procesamiento: {e}")
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text="❌ *Error crítico:* No se pudo procesar la tarjeta. Contacta con soporte.",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error en comando br: {e}")
        await update.message.reply_text("❌ *Error inesperado:* Intenta nuevamente o contacta con soporte.", parse_mode='Markdown')

# Exportar el handler para registro
br_handler = CommandHandler("br", br)