import os
from funcionamiento.usuarios import es_administrador

async def ppconfig(update, context):
    """Configurar API de PayPal (solo admin)"""
    user_id = str(update.effective_user.id)
    
    if not es_administrador(user_id):
        await update.message.reply_text("❌ Solo administradores pueden configurar PayPal.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: /ppconfig <client_id> <client_secret>")
        return
    
    client_id = context.args[0]
    client_secret = context.args[1]
    
    # Guardar en variables de entorno
    os.environ['PAYPAL_CLIENT_ID'] = client_id
    os.environ['PAYPAL_CLIENT_SECRET'] = client_secret
    
    await update.message.reply_text("✅ PayPal configurado correctamente.")