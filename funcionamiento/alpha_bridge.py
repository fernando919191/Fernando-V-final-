import asyncio
import re
from datetime import datetime

# Diccionario para trackear mensajes en proceso
mensajes_pendientes = {}

async def enviar_a_alpha(bot, chat_id, cc_data, message_id):
    """Envía comando a @Alphachekerbot y monitoriza respuesta"""
    try:
        # Guardar referencia del mensaje original
        mensajes_pendientes[message_id] = {
            'chat_id': chat_id,
            'cc_data': cc_data,
            'timestamp': datetime.now()
        }
        
        # Enviar mensaje a @Alphachekerbot
        await bot.send_message(
            chat_id='@Alphachekerbot',  # ⚠️ Verificar el username exacto
            text=f"/bn {cc_data}"
        )
        
        return True
        
    except Exception as e:
        print(f"Error enviando a Alpha: {e}")
        return False

def parsear_respuesta_alpha(texto):
    """Parsea la respuesta de @Alphachekerbot"""
    try:
        # Extraer información con regex
        cc_match = re.search(r'CC:\s*([\d\|]+)', texto)
        status_match = re.search(r'Status:\s*(.+?)\n', texto)
        response_match = re.search(r'Response:\s*(.+?)\n', texto)
        country_match = re.search(r'Country:\s*(.+?)\n', texto)
        bank_match = re.search(r'Bank:\s*(.+?)\n', texto)
        type_match = re.search(r'Type:\s*(.+?)\n', texto)
        
        return {
            'cc': cc_match.group(1) if cc_match else 'N/A',
            'status': status_match.group(1) if status_match else 'N/A',
            'response': response_match.group(1) if response_match else 'N/A',
            'country': country_match.group(1) if country_match else 'N/A',
            'bank': bank_match.group(1) if bank_match else 'N/A',
            'type': type_match.group(1) if type_match else 'N/A',
            'bin': cc_match.group(1).split('|')[0][:6] if cc_match else 'N/A'
        }
        
    except Exception as e:
        print(f"Error parseando respuesta: {e}")
        return None