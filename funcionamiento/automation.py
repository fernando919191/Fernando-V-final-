import asyncio
from telethon import TelegramClient, events
import os

# Configuración de API de Telegram (obtener de https://my.telegram.org)
API_ID = os.environ.get('TELEGRAM_API_ID', '')
API_HASH = os.environ.get('TELEGRAM_API_HASH', '')
PHONE_NUMBER = os.environ.get('TELEGRAM_PHONE_NUMBER', '')

# Variable global para el cliente
client = None

def iniciar_automation():
    """Inicia el cliente de Telethon para automatización"""
    global client
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        print("❌ Faltan credenciales de Telegram API")
        return None
    
    try:
        client = TelegramClient('bot_session', int(API_ID), API_HASH)
        return client
    except Exception as e:
        print(f"❌ Error iniciando Telethon: {e}")
        return None

async def enviar_a_bot_secundario(bot_username, cc_data):
    """Envía comando al bot secundario y espera respuesta"""
    try:
        # Enviar comando al bot secundario
        await client.send_message(bot_username, f"/bn {cc_data}")
        
        # Esperar respuesta (timeout de 30 segundos)
        response = await esperar_respuesta_bot(bot_username, timeout=30)
        return response
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def esperar_respuesta_bot(bot_username, timeout=30):
    """Espera la respuesta del bot secundario"""
    try:
        # Esperar mensaje del bot
        async with client.conversation(bot_username, timeout=timeout) as conv:
            response = await conv.get_response()
            return response.text
    except asyncio.TimeoutError:
        return "❌ Timeout: El bot no respondió"
    except Exception as e:
        return f"❌ Error esperando respuesta: {str(e)}"