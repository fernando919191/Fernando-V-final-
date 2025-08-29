import asyncio
from telethon import TelegramClient
import os

# Configuración desde variables de entorno
API_ID = os.environ.get('28812767')
API_HASH = os.environ.get('29bca7d6dbc1f6b9d14a9182fb2bcf42') 
PHONE_NUMBER = os.environ.get('+523741487538')

client = None

def iniciar_automation():
    """Inicia el cliente de Telethon"""
    global client
    try:
        if not all([API_ID, API_HASH, PHONE_NUMBER]):
            return None
            
        client = TelegramClient('bot_session', int(API_ID), API_HASH)
        return client
    except Exception as e:
        print(f"❌ Error iniciando Telethon: {e}")
        return None

async def enviar_a_bot_secundario(bot_username, cc_data):
    """Envía comando al bot secundario"""
    try:
        if not client:
            return "❌ Cliente no inicializado"
            
        await client.send_message(bot_username, f"/bn {cc_data}")
        response = await esperar_respuesta_bot(bot_username)
        return response
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def esperar_respuesta_bot(bot_username, timeout=30):
    """Espera la respuesta del bot"""
    try:
        async with client.conversation(bot_username, timeout=timeout) as conv:
            response = await conv.get_response()
            return response.text
    except asyncio.TimeoutError:
        return "❌ Timeout: El bot no respondió"
    except Exception as e:
        return f"❌ Error: {str(e)}"