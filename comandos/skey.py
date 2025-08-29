import os
from funcionamiento.usuarios import es_administrador

async def skey(update, context):
    """Configurar Stripe Secret Key (solo admin)"""
    user_id = str(update.effective_user.id)
    
    if not es_administrador(user_id):
        await update.message.reply_text("❌ Solo administradores pueden configurar Stripe.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Uso: /skey <stripe_secret_key>")
        return
    
    stripe_key = context.args[0]
    
    # Guardar en variable de entorno (o en base de datos)
    os.environ['STRIPE_SECRET_KEY'] = stripe_key
    
    await update.message.reply_text("✅ Stripe Secret Key configurada correctamente.")