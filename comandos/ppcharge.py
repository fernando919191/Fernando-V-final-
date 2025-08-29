import os
import asyncio
import paypalrestsdk
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

# Configurar PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # "sandbox" o "live"
    "client_id": os.environ.get('PAYPAL_CLIENT_ID', ''),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET', '')
})

# Estado para la conversación
CONFIRMACION = 1

async def ppcharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Microcharge de $20 MXN con PayPal"""
    user_id = update.effective_user.id
    
    # Verificar licencia
    from funcionamiento.licencias import usuario_tiene_licencia_activa
    if not usuario_tiene_licencia_activa(user_id):
        await update.message.reply_text("❌ Necesitas una licencia activa para usar este comando.")
        return ConversationHandler.END
    
    # Verificar formato de tarjeta
    if not context.args:
        await update.message.reply_text("❌ Uso: /ppcharge <cc|mm|yy|cvv>")
        return ConversationHandler.END
    
    try:
        cc_data = ' '.join(context.args).split('|')
        if len(cc_data) != 4:
            await update.message.reply_text("❌ Formato incorrecto. Usa: /ppcharge 4111111111111111|12|25|123")
            return ConversationHandler.END
        
        cc, mm, yy, cvv = cc_data
        
        # Guardar datos en context
        context.user_data['cc_data'] = (cc, mm, yy, cvv)
        
        # ADVERTENCIA LEGAL
        advertencia = (
            "⚠️ **ADVERTENCIA LEGAL**:\n\n"
            "• Solo verifica tarjetas PROPIAS\n"
            "• Se realizará un cargo de $20.00 MXN\n"
            "• El cargo NO será reembolsado automáticamente\n"
            "• Fees de PayPal: $7.90 MXN\n"
            "• Recibirás: $12.10 MXN netos\n\n"
            "¿Continuar? (sí/no)"
        )
        
        await update.message.reply_text(advertencia)
        return CONFIRMACION
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END

async def confirmar_ppcharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la confirmación del microcharge"""
    respuesta = update.message.text.lower()
    
    if respuesta not in ['sí', 'si', 'yes', 'y']:
        await update.message.reply_text("❌ Operación cancelada.")
        return ConversationHandler.END
    
    # Obtener datos de la tarjeta
    cc, mm, yy, cvv = context.user_data['cc_data']
    
    # Mostrar mensaje de procesamiento
    msg = await update.message.reply_text("🔄 Realizando microcharge de $20.00 MXN...")
    
    # Intentar microcharge
    result = await realizar_microcharge_paypal(cc, mm, yy, cvv)
    
    if result["success"]:
        await msg.edit_text(
            f"✅ **Microcharge EXITOSO**\n\n"
            f"💳 **Tarjeta:** `{cc}`\n"
            f"💸 **Monto:** $20.00 MXN\n"
            f"🏦 **Banco:** {result.get('bank', 'N/A')}\n"
            f"🇲🇽 **País:** {result.get('country', 'N/A')}\n"
            f"📞 **Marca:** {result.get('brand', 'N/A')}\n"
            f"🔢 **Últimos 4:** {result.get('last4', 'N/A')}\n"
            f"💰 **Neto recibido:** $12.10 MXN\n\n"
            f"✅ **La tarjeta TIENE fondos y es VÁLIDA**"
        )
    else:
        await msg.edit_text(
            f"❌ **Microcharge FALLIDO**\n\n"
            f"💳 **Tarjeta:** `{cc}`\n"
            f"💸 **Monto:** $20.00 MXN\n"
            f"🚫 **Error:** {result.get('error', 'Error desconocido')}\n\n"
            f"💔 **La tarjeta NO tiene fondos o es INVÁLIDA**"
        )
    
    return ConversationHandler.END

async def cancelar_ppcharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la operación"""
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

async def realizar_microcharge_paypal(cc, mm, yy, cvv, amount=20.00):
    """Realiza un microcharge de $20 MXN con PayPal"""
    try:
        # Detectar tipo de tarjeta
        card_type = "visa"  # Por defecto
        if cc.startswith('5'):
            card_type = "mastercard"
        elif cc.startswith('3'):
            card_type = "amex"
        elif cc.startswith('6'):
            card_type = "discover"
        
        # Crear pago
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "credit_card",
                "funding_instruments": [{
                    "credit_card": {
                        "number": cc,
                        "type": card_type,
                        "expire_month": int(mm),
                        "expire_year": int(yy),
                        "cvv2": cvv,
                        "first_name": "Test",
                        "last_name": "User"
                    }
                }]
            },
            "transactions": [{
                "amount": {
                    "total": str(amount),
                    "currency": "MXN"
                },
                "description": "Verificación de tarjeta - Microcharge"
            }]
        })
        
        # Ejecutar pago
        if payment.create():
            return {
                "success": True,
                "message": "Pago exitoso",
                "brand": card_type.upper(),
                "last4": cc[-4:],
                "country": "MX",
                "bank": "N/A",
                "payment_id": payment.id
            }
        else:
            return {
                "success": False,
                "message": "Pago fallido",
                "error": payment.error.message if payment.error else "Error desconocido"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": "Error PayPal",
            "error": str(e)
        }

def setup(application):
    """Configura el ConversationHandler para /ppcharge"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("ppcharge", ppcharge)],
        states={
            CONFIRMACION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_ppcharge)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancelar_ppcharge)],
        allow_reentry=True
    )
    
    return conv_handler