from telegram import Update
from telegram.ext import ContextTypes
import requests
import json

async def bin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para verificar información de BIN de tarjetas"""
    
    if not context.args:
        await update.message.reply_text("❌ Debes proporcionar un BIN. Ejemplo: /bin 123456")
        return
    
    bin_input = context.args[0].strip()
    
    if not bin_input.isdigit() or len(bin_input) < 6:
        await update.message.reply_text("❌ El BIN debe ser numérico y tener al menos 6 dígitos.")
        return
    
    # Tomar solo los primeros 6 dígitos por seguridad
    bin_input = bin_input[:6]
    
    try:
        # API ALTERNATIVA 1 - Binlist.net (gratuita y funciona)
        response = requests.get(
            f"https://lookup.binlist.net/{bin_input}",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer información
            banco = data.get('bank', {}).get('name', 'Desconocido')
            pais = data.get('country', {}).get('name', 'Desconocido')
            marca = data.get('scheme', 'Desconocido').upper()
            tipo = data.get('type', 'Desconocido').capitalize()
            bandera = data.get('country', {}).get('emoji', '')
            
            respuesta = f"""
💳 *Información del BIN*: `{bin_input}`
• 🏦 *Banco*: {banco}
• 🌎 *País*: {pais} {bandera}
• 🏷️ *Marca*: {marca}
• 🔧 *Tipo*: {tipo}
• ✅ *BIN válido*: Sí
            """
            
        else:
            # API ALTERNATIVA 2 - Si la primera falla
            response2 = requests.get(f"https://bin-ip-checker.p.rapidapi.com/?bin={bin_input}", headers={
                "X-RapidAPI-Key": "free",  # Key gratuita
                "X-RapidAPI-Host": "bin-ip-checker.p.rapidapi.com"
            })
            
            if response2.status_code == 200:
                data = response2.json()
                respuesta = f"""
💳 *Información del BIN*: `{bin_input}`
• 🏦 *Banco*: {data.get('bank', {}).get('name', 'Desconocido')}
• 🌎 *País*: {data.get('country', {}).get('name', 'Desconocido')}
• 🏷️ *Marca*: {data.get('scheme', 'Desconocido')}
• 🔧 *Tipo*: {data.get('type', 'Desconocido')}
• ✅ *BIN válido*: Sí
                """
            else:
                respuesta = "❌ BIN no encontrado en nuestras bases de datos."
        
        await update.message.reply_text(respuesta, parse_mode='Markdown')
            
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Error de conexión: {str(e)}")
    except json.JSONDecodeError:
        await update.message.reply_text("❌ Error al procesar la respuesta del servidor.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error inesperado: {str(e)}")