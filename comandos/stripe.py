import os
import stripe
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# Configurar Stripe
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_tu_key_aqui')
stripe.api_key = STRIPE_SECRET_KEY

async def stripe_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gate de Stripe para verificar tarjetas"""
    user_id = update.effective_user.id
    
    # Verificar licencia
    from funcionamiento.licencias import usuario_tiene_licencia_activa
    if not usuario_tiene_licencia_activa(user_id):
        await update.message.reply_text("❌ Necesitas una licencia activa para usar este comando.")
        return
    
    # Verificar formato de tarjeta
    if not context.args:
        await update.message.reply_text("❌ Uso: /stripe <cc|mm|yy|cvv>")
        return
    
    try:
        cc_data = ' '.join(context.args).split('|')
        if len(cc_data) != 4:
            await update.message.reply_text("❌ Formato incorrecto. Usa: /stripe 4111111111111111|12|25|123")
            return
        
        cc, mm, yy, cvv = cc_data
        
        # Mostrar mensaje de procesamiento
        msg = await update.message.reply_text("🔄 Probando tarjeta en Stripe...")
        
        # Intentar crear payment method
        payment_method = await crear_payment_method(cc, mm, yy, cvv)
        
        if payment_method:
            # Intentar crear pago de prueba
            result = await intentar_pago(payment_method.id)
            
            if result["success"]:
                await msg.edit_text(
                    f"✅ **Stripe Gate - APROBADA**\n\n"
                    f"💳 **Tarjeta:** `{cc}`\n"
                    f"🔄 **Response:** {result['message']}\n"
                    f"🏦 **Bank:** {result.get('bank', 'N/A')}\n"
                    f"🇵 **Country:** {result.get('country', 'N/A')}\n"
                    f"📞 **Brand:** {result.get('brand', 'N/A')}\n"
                    f"💸 **Tipo:** {result.get('funding', 'N/A')}"
                )
            else:
                await msg.edit_text(
                    f"❌ **Stripe Gate - DECLINADA**\n\n"
                    f"💳 **Tarjeta:** `{cc}`\n"
                    f"🔄 **Response:** {result['message']}\n"
                    f"🚫 **Error:** {result.get('error', 'N/A')}"
                )
        else:
            await msg.edit_text("❌ Error al crear payment method. Tarjeta inválida.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def crear_payment_method(cc, mm, yy, cvv):
    """Crea un payment method en Stripe"""
    try:
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": cc,
                "exp_month": int(mm),
                "exp_year": int(yy),
                "cvc": cvv,
            },
        )
        return payment_method
    except stripe.error.StripeError as e:
        print(f"Stripe Error: {e}")
        return None

async def intentar_pago(payment_method_id, amount=100):
    """Intenta un pago de prueba ($1.00)"""
    try:
        # Crear intento de pago
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,  # $1.00
            currency="usd",
            payment_method=payment_method_id,
            confirmation_method="manual",
            confirm=True,
        )
        
        # Analizar respuesta
        if payment_intent.status == "succeeded":
            return {
                "success": True,
                "message": "Pago exitoso",
                "brand": payment_intent.payment_method.card.brand,
                "country": payment_intent.payment_method.card.country,
                "bank": payment_intent.payment_method.card.bank,
                "funding": payment_intent.payment_method.card.funding,
            }
        else:
            return {
                "success": False,
                "message": payment_intent.status,
                "error": payment_intent.last_payment_error.message if payment_intent.last_payment_error else "Unknown error"
            }
            
    except stripe.error.CardError as e:
        return {
            "success": False,
            "message": "Card declined",
            "error": e.error.message
        }
    except stripe.error.StripeError as e:
        return {
            "success": False,
            "message": "Stripe error",
            "error": str(e)
        }