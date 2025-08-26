from telegram import Update
from telegram.ext import ContextTypes
import requests
import json

async def bin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para verificar información de BIN de tarjetas"""
    
    # Verificar si se proporcionó un BIN
    if not context.args:
        await update.message.reply_text("❌ Debes proporcionar un BIN. Ejemplo: /bin 123456")
        return
    
    bin_input = context.args[0].strip()
    
    # Validar el BIN
    if not bin_input.isdigit() or len(bin_input) < 6:
        await update.message.reply_text("❌ El BIN debe ser numérico y tener al menos 6 dígitos.")
        return
    
    try:
        # Consultar la API de BIN
        response = requests.get(f"https://data.handyapi.com/bin/{bin_input}")
        response.raise_for_status()
        api_data = response.json()

        if api_data.get("Status") == "SUCCESS":
            # Extraer información
            pais = api_data["Country"]["Name"]
            marca = api_data["Scheme"]
            tipo = api_data["Type"]
            nivel = api_data["CardTier"]
            banco = api_data["Issuer"]

            # Formatear respuesta
            respuesta = f"""
💳 *Información del BIN*: `{bin_input}`
• 🏦 *Banco*: {banco}
• 🌎 *País*: {pais}
• 🏷️ *Marca*: {marca}
• 🔧 *Tipo*: {tipo}
• ⭐ *Nivel*: {nivel}
            """
            
            await update.message.reply_text(respuesta, parse_mode='Markdown')
            
        else:
            await update.message.reply_text("❌ BIN no válido o no encontrado.")

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Error de conexión: {str(e)}")
    except json.JSONDecodeError:
        await update.message.reply_text("❌ Error al procesar la respuesta del servidor.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error inesperado: {str(e)}")