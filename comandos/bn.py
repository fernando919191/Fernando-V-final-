import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.alpha_bridge import enviar_a_alpha

async def bn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso con @Alphachekerbot"""
    user_id = update.effective_user.id
    
    # Verificar licencia
    from funcionamiento.licencias import usuario_tiene_licencia_activa
    if not usuario_tiene_licencia_activa(user_id):
        await update.message.reply_text("❌ Necesitas una licencia activa.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Uso: /bn <cc|mm|yy|cvv>")
        return
    
    try:
        cc_data = ' '.join(context.args)
        cc_parts = cc_data.split('|')
        
        if len(cc_parts) != 4:
            await update.message.reply_text("❌ Formato incorrecto. Usa: /bn 4111111111111111|12|25|123")
            return
        
        cc, mm, yy, cvv = cc_parts
        
        # Mensaje de que se está enviando a Alpha
        msg = await update.message.reply_text(
            f"🔄 **Enviando a @Alphachekerbot...**\n\n"
            f"💳 **Tarjeta:** `{cc}`\n"
            f"📅 **Expira:** {mm}/{yy}\n"
            f"🔢 **CVV:** {cvv}\n\n"
            f"⏳ Esperando respuesta de Alpha...",
            parse_mode='Markdown'
        )
        
        # Enviar a Alpha y guardar referencia
        success = await enviar_a_alpha(
            context.bot,
            update.effective_chat.id,
            cc_data,
            msg.message_id
        )
        
        if not success:
            await msg.edit_text("❌ Error conectando con @Alphachekerbot")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")