import os
import asyncio
import paypalrestsdk
from telegram import Update
from telegram.ext import ContextTypes

async def ppcharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Microcharge de $20 MXN con PayPal"""
    
    # Verificar si PayPal está configurado
    client_id = os.environ.get('PAYPAL_CLIENT_ID')
    client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        await update.message.reply_text(
            "❌ PayPal no está configurado.\n\n"
            "Usa primero: /ppconfig <client_id> <client_secret>\n"
            "O configura las variables de entorno PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET"
        )
        return
    
    # Configurar PayPal con las credenciales
    paypalrestsdk.configure({
        "mode": "sandbox",  # "sandbox" o "live"
        "client_id": client_id,
        "client_secret": client_secret
    })
    
    user_id = update.effective_user.id
    
    # Verificar licencia
    from funcionamiento.licencias import usuario_tiene_licencia_activa
    if not usuario_tiene_licencia_activa(user_id):
        await update.message.reply_text("❌ Necesitas una licencia activa para usar este comando.")
        return
    
    # Verificar formato de tarjeta
    if not context.args:
        await update.message.reply_text("❌ Uso: /ppcharge <cc|mm|yy|cvv>")
        return
    
    try:
        cc_data = ' '.join(context.args).split('|')
        if len(cc_data) != 4:
            await update.message.reply_text("❌ Formato incorrecto. Usa: /ppcharge 4111111111111111|12|25|123")
            return
        
        cc, mm, yy, cvv = cc_data
        
        # Mostrar mensaje de procesamiento inmediato
        mensaje_procesando = (
            f"🔄 **Procesando tarjeta...**\n\n"
            f"💳 **Tarjeta:** `{cc}`\n"
            f"📅 **Expira:** {mm}/{yy}\n"
            f"🔢 **CVV:** {cvv}\n"
            f"💸 **Monto:** $20.00 MXN\n\n"
            f"⏳ Verificando fondos..."
        )
        
        msg = await update.message.reply_text(mensaje_procesando, parse_mode='Markdown')
        
        # Intentar microcharge
        result = await realizar_microcharge_paypal(cc, mm, yy, cvv)
        
        if result["success"]:
            await msg.edit_text(
                f"✅ **Microcharge EXITOSO**\n\n"
                f"💳 **Tarjeta:** `{cc}`\n"
                f"📅 **Expira:** {mm}/{yy}\n"
                f"🔢 **CVV:** {cvv}\n"
                f"💸 **Monto:** $20.00 MXN\n"
                f"🏦 **Banco:** {result.get('bank', 'N/A')}\n"
                f"🇲🇽 **País:** {result.get('country', 'N/A')}\n"
                f"📞 **Marca:** {result.get('brand', 'N/A')}\n"
                f"🔢 **Últimos 4:** {result.get('last4', 'N/A')}\n"
                f"💰 **Neto recibido:** $12.10 MXN\n\n"
                f"✅ **La tarjeta TIENE fondos y es VÁLIDA**",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                f"❌ **Microcharge FALLIDO**\n\n"
                f"💳 **Tarjeta:** `{cc}`\n"
                f"📅 **Expira:** {mm}/{yy}\n"
                f"🔢 **CVV:** {cvv}\n"
                f"💸 **Monto:** $20.00 MXN\n"
                f"🚫 **Error:** {result.get('error', 'Error desconocido')}\n\n"
                f"💔 **La tarjeta NO tiene fondos o es INVÁLIDA**",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def realizar_microcharge_paypal(cc, mm, yy, cvv, amount=20.00):
    """Realiza un microcharge de $20 MXN con PayPal"""
    try:
        # Configurar PayPal con las credenciales actuales
        client_id = os.environ.get('PAYPAL_CLIENT_ID')
        client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        
        paypalrestsdk.configure({
            "mode": "sandbox",
            "client_id": client_id,
            "client_secret": client_secret
        })
        
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