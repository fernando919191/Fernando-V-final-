import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from funcionamiento.usuarios import obtener_info_usuario_completa
from utils.braintree_processor import braintree_processor, ErrorType

logger = logging.getLogger(__name__)

async def br(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /br command for Braintree credit card processing"""
    try:
        user_id = str(update.effective_user.id)
        
        # Check if user is premium
        user_info = obtener_info_usuario_completa(user_id)
        if not user_info or not user_info.get('es_premium', False):
            await update.message.reply_text(
                "❌ *Acceso restringido*\n\n"
                "Este comando es solo para usuarios premium. "
                "Usa `/key <clave>` para canjear una licencia.",
                parse_mode='Markdown'
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ *Formato incorrecto*\n\n"
                "• Use: `/br CC|MM|YYYY|CVV`\n"
                "• Ejemplo: `/br 5265577028194567|09|2029|835`\n"
                "• Separe con: `|` `/` `-` o espacio",
                parse_mode='Markdown'
            )
            return
        
        cc_text = ' '.join(context.args)
        
        # Validate format first
        is_valid, cc_data, format_error = braintree_processor.validate_cc_format(cc_text)
        if not is_valid:
            await update.message.reply_text(
                f"🔴 *{ErrorType.INVALID_FORMAT.value}*\n\n"
                f"`{format_error}`\n\n"
                "• Formato: `CC|MM|YYYY|CVV`\n"
                "• Ejemplo: `5265577028194567|09|2029|835`",
                parse_mode='Markdown'
            )
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔄 *Procesando tarjeta en Braintree...*\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "⏰ _Timeout: 15 segundos_",
            parse_mode='Markdown'
        )
        
        try:
            # Get BIN info and process payment concurrently
            bin_info_task = braintree_processor.get_bin_info(cc_data['cc'])
            payment_task = braintree_processor.simulate_api_call(cc_data)
            
            # Wait for both tasks with timeout
            done, pending = await asyncio.wait(
                [bin_info_task, payment_task],
                timeout=15,  # 15 second timeout
                return_when=asyncio.ALL_COMPLETED
            )
            
            # Cancel pending tasks if timeout
            for task in pending:
                task.cancel()
            
            # Process results
            bin_info, bin_error = None, None
            payment_success, payment_msg, error_type = False, "", None
            
            for task in done:
                try:
                    result = task.result()
                    if isinstance(result, tuple) and len(result) == 2:  # bin_info result
                        bin_info, bin_error = result
                    elif isinstance(result, tuple) and len(result) == 3:  # payment result
                        payment_success, payment_msg, error_type = result
                except asyncio.TimeoutError:
                    payment_success, payment_msg, error_type = False, "❌ Timeout de conexión (15s)", ErrorType.CONNECTION_ERROR
                except Exception as e:
                    logger.error(f"Error processing task: {e}")
                    payment_success, payment_msg, error_type = False, "❌ Error interno de procesamiento", ErrorType.INTERNAL_ERROR
            
            # Handle BIN error (non-critical, we can continue)
            if bin_error:
                logger.warning(f"BIN info error: {bin_error}")
            
            # Format and send response
            if payment_success:
                response = braintree_processor.format_success_response(cc_data, bin_info, payment_msg)
            else:
                response = braintree_processor.format_error_response(cc_data, error_type, payment_msg)
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=response,
                parse_mode='Markdown'
            )
            
        except asyncio.TimeoutError:
            error_response = braintree_processor.format_error_response(
                cc_data, 
                ErrorType.CONNECTION_ERROR, 
                "❌ Timeout de conexión (15 segundos)"
            )
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=error_response,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in br command: {e}")
            error_response = braintree_processor.format_error_response(
                cc_data, 
                ErrorType.INTERNAL_ERROR, 
                "❌ Error interno del sistema"
            )
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=error_response,
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in br command: {e}")
        await update.message.reply_text(
            "❌ *Error crítico*\n\n"
            "No se pudo procesar el comando. "
            "Intenta nuevamente o contacta con soporte.",
            parse_mode='Markdown'
        )

# Exportar el handler para registro
br_handler = CommandHandler("br", br)