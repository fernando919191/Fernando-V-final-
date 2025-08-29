import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.automation import enviar_a_bot_secundario, iniciar_automation

# Configuración del bot secundario
BOT_SECUNDARIO = "@otrobot"  # Reemplaza con el username del bot real

async def bn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía tarjeta a bot secundario para procesamiento"""
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
        
        # Mostrar mensaje de procesamiento
        msg = await update.message.reply_text(
            f"🔄 **Procesando tarjeta...**\n\n"
            f"💳 **Tarjeta:** `{cc_data.split('|')[0]}`\n"
            f"📅 **Expira:** {cc_data.split('|')[1]}/{cc_data.split('|')[2]}\n"
            f"🔢 **CVV:** {cc_data.split('|')[3]}\n\n"
            f"⏳ Enviando a bot secundario...",
            parse_mode='Markdown'
        )
        
        # Iniciar automation si no está iniciado
        client = iniciar_automation()
        if not client:
            await msg.edit_text("❌ Error: Automation no configurado.")
            return
        
        # Enviar al bot secundario
        async with client:
            response = await enviar_a_bot_secundario(BOT_SECUNDARIO, cc_data)
        
        # Parsear respuesta
        bin_info = cc_data.split('|')[0][:6]
        respuesta_final = f"✅ **Respuesta del Bot:**\n\n{response}\n\n🔢 **BIN:** {bin_info}"
        
        await msg.edit_text(respuesta_final, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")