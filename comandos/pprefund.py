import paypalrestsdk
import os
from funcionamiento.usuarios import es_administrador

async def pprefund(update, context):
    """Reembolsar microcharge de PayPal (solo admin)"""
    user_id = str(update.effective_user.id)
    
    if not es_administrador(user_id):
        await update.message.reply_text("❌ Solo administradores pueden hacer reembolsos.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Uso: /pprefund <payment_id>")
        return
    
    payment_id = context.args[0]
    
    try:
        # Obtener el pago
        payment = paypalrestsdk.Payment.find(payment_id)
        
        # Crear reembolso
        refund = payment.refund({})
        
        if refund.success():
            await update.message.reply_text(
                f"✅ Reembolso exitoso\n\n"
                f"🔢 **Payment ID:** {payment_id}\n"
                f"💰 **Monto reembolsado:** $20.00 MXN\n"
                f"📋 **Estado:** {refund.state}"
            )
        else:
            await update.message.reply_text(f"❌ Error al reembolsar: {refund.error.message}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")