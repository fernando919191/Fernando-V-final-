import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.automation import enviar_a_bot_secundario, iniciar_automation

# ⚠️ REEMPLAZA con el username REAL del bot secundario
BOT_SECUNDARIO = "@NombreDelBotSecundarioBot"  # Ejemplo: "@MyCheckerBot"

async def bn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía tarjeta a bot secundario"""
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
        
        # Mensaje de procesamiento
        msg = await update.message.reply_text(
            f"🔄 **Procesando tarjeta...**\n\n"
            f"💳 **Tarjeta:** `{cc}`\n"
            f"📅 **Expira:** {mm}/{yy}\n"
            f"🔢 **CVV:** {cvv}\n\n"
            f"⏳ Enviando a bot secundario...",
            parse_mode='Markdown'
        )
        
        # Iniciar automation
        client = iniciar_automation()
        if not client:
            await msg.edit_text("❌ Error: Sistema de automation no disponible.")
            return
        
        # Enviar y esperar respuesta
        async with client:
            await client.start(PHONE_NUMBER)
            response = await enviar_a_bot_secundario(BOT_SECUNDARIO, cc_data)
        
        # Mostrar resultado
        bin_info = cc[:6]
        await msg.edit_text(
            f"✅ **Resultado:**\n\n{response}\n\n🔢 **BIN:** {bin_info}",
            parse_mode='Markdown'
        )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")