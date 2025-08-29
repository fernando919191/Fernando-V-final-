import os
import stripe
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

# Configurar Stripe
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_tu_key_aqui')
stripe.api_key = STRIPE_SECRET_KEY

async def microcharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Microcharge de $0.50 para verificar fondos reales"""
    user_id = update.effective_user.id
    
    # Verificar licencia
    from funcionamiento.licencias import usuario_tiene_licencia_activa
    if not usuario_tiene_licencia_activa(user_id):
        await update.message.reply_text("❌ Necesitas una licencia activa para usar este comando.")
        return
    
    # Verificar formato de tarjeta
    if not context.args:
        await update.message.reply_text("❌ Uso: /charge <cc|mm|yy|cvv>")
        return
    
    try:
        cc_data = ' '.join(context.args).split('|')
        if len(cc_data) != 4:
            await update.message.reply_text("❌ Formato incorrecto. Usa: /charge 4111111111111111|12|25|123")
            return
        
        cc, mm, yy, cvv = cc_data
        
        # ADVERTENCIA LEGAL
        advertencia = (
            "⚠️ **ADVERTENCIA LEGAL**:\n\n"
            "• Solo verifica tarjetas PROPIAS\n"
            "• Se realizará un cargo de $0.50\n"
            "• El cargo NO será reembolsado automáticamente\n"
            "• Usa bajo tu propia responsabilidad\n\n"
            "¿Continuar? (sí/no)"
        )
        
        await update.message.reply_text(advertencia)
        
        # Esperar confirmación
        def check_confirm(update):
            return update.message.text.lower() in ['sí', 'si', 'yes', 'y']
        
        try:
            confirm = await context.application.update_queue.get()
            if not check_confirm(confirm):
                await update.message.reply_text("❌ Operación cancelada.")
                return
        except asyncio.TimeoutError:
            await update.message.reply_text("❌ Tiempo de confirmación agotado.")
            return
        
        # Mostrar mensaje de procesamiento
        msg = await update.message.reply_text("🔄 Realizando microcharge de $0.50...")
        
        # Intentar microcharge
        result = await realizar_microcharge(cc, mm, yy, cvv)
        
        if result["success"]:
            await msg.edit_text(
                f"✅ **Microcharge EXITOSO**\n\n"
                f"💳 **Tarjeta:** `{cc}`\n"
                f"💸 **Monto:** $0.50\n"
                f"🏦 **Banco:** {result.get('bank', 'N/A')}\n"
                f"🇵 **Country:** {result.get('country', 'N/A')}\n"
                f"📞 **Brand:** {result.get('brand', 'N/A')}\n"
                f"🔢 **Últimos 4:** {result.get('last4', 'N/A')}\n\n"
                f"💰 **La tarjeta TIENE fondos y es VÁLIDA**"
            )
        else:
            await msg.edit_text(
                f"❌ **Microcharge FALLIDO**\n\n"
                f"💳 **Tarjeta:** `{cc}`\n"
                f"💸 **Monto:** $0.50\n"
                f"🚫 **Error:** {result.get('error', 'Error desconocido')}\n\n"
                f"💔 **La tarjeta NO tiene fondos o es INVÁLIDA**"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def realizar_microcharge(cc, mm, yy, cvv, amount=50):
    """Realiza un microcharge de $0.50 (50 centavos)"""
    try:
        # Crear customer
        customer = stripe.Customer.create()
        
        # Crear payment method
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": cc,
                "exp_month": int(mm),
                "exp_year": int(yy),
                "cvc": cvv,
            },
        )
        
        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method.id,
            customer=customer.id,
        )
        
        # Set as default payment method
        stripe.Customer.modify(
            customer.id,
            invoice_settings={
                "default_payment_method": payment_method.id,
            },
        )
        
        # Crear payment intent de $0.50
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,  # $0.50 (50 centavos)
            currency="usd",
            customer=customer.id,
            payment_method=payment_method.id,
            confirmation_method="manual",
            confirm=True,
            metadata={
                "tipo": "verificacion_microcharge",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Analizar respuesta
        if payment_intent.status == "succeeded":
            return {
                "success": True,
                "message": "Microcharge exitoso",
                "brand": payment_intent.payment_method.card.brand,
                "country": payment_intent.payment_method.card.country,
                "bank": payment_intent.payment_method.card.bank,
                "last4": payment_intent.payment_method.card.last4,
                "funding": payment_intent.payment_method.card.funding,
                "charge_id": payment_intent.id
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