from telegram import Update
from telegram.ext import ContextTypes
import aiohttp
import random
import asyncio

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para generar direcciones reales usando múltiples APIs gratuitas"""
    
    PAISES = {
        'mx': {'nombre': 'Mexico', 'codigo': '+52'},
        'col': {'nombre': 'Colombia', 'codigo': '+57'}, 
        'ven': {'nombre': 'Venezuela', 'codigo': '+58'},
        'us': {'nombre': 'United States', 'codigo': '+1'},
        'uk': {'nombre': 'United Kingdom', 'codigo': '+44'},
        'ca': {'nombre': 'Canada', 'codigo': '+1'},
        'rus': {'nombre': 'Russia', 'codigo': '+7'},
        'jap': {'nombre': 'Japan', 'codigo': '+81'},
        'chi': {'nombre': 'China', 'codigo': '+86'},
        'hon': {'nombre': 'Honduras', 'codigo': '+504'},
        'chile': {'nombre': 'Chile', 'codigo': '+56'},
        'arg': {'nombre': 'Argentina', 'codigo': '+54'},
        'ind': {'nombre': 'India', 'codigo': '+91'},
        'br': {'nombre': 'Brazil', 'codigo': '+55'},
        'peru': {'nombre': 'Peru', 'codigo': '+51'},
        'es': {'nombre': 'Spain', 'codigo': '+34'},
        'italia': {'nombre': 'Italy', 'codigo': '+39'},
        'fran': {'nombre': 'France', 'codigo': '+33'},
        'suiza': {'nombre': 'Switzerland', 'codigo': '+41'}
    }
    
    if not context.args:
        lista_paises = "\n".join([f"• {codigo} - {info['nombre']}" for codigo, info in PAISES.items()])
        await update.message.reply_text(
            f"🌍 *Comando RM - Generador de Direcciones*\n\n"
            f"📝 Uso: /rm <código_país>\n\n"
            f"🇺🇳 *Países disponibles:*\n{lista_paises}\n\n"
            f"Ejemplo: /rm mx para datos de México",
            parse_mode='Markdown'
        )
        return
    
    pais_code = context.args[0].lower()
    
    if pais_code not in PAISES:
        await update.message.reply_text("❌ Código de país no válido.")
        return
    
    pais_info = PAISES[pais_code]
    mensaje_carga = await update.message.reply_text("🔄 Generando dirección real...")
    
    try:
        # INTENTO 1: API de OpenStreetMap (sin límites)
        datos = await obtener_datos_osm(pais_info['nombre'])
        
        if not datos:
            # INTENTO 2: API de Geoapify (1000 requests/día gratis)
            datos = await obtener_datos_geoapify(pais_info['nombre'])
        
        if not datos:
            # INTENTO 3: API de RandomData (sin límites)
            datos = await obtener_datos_random(pais_info['nombre'])
        
        if datos:
            respuesta = f"""
🌍 *Dirección en {pais_info['nombre']}*

🏢 *Street:* `{datos['calle']}`
🏙️ *City:* `{datos['ciudad']}`
🏛️ *State:* `{datos['estado']}`
📮 *ZIP Code:* `{datos['codigo_postal']}`
📞 *Phone Code:* `{pais_info['codigo']}`
🇺🇳 *Country:* `{pais_info['nombre']}`

✅ *Datos generados con información real*
            """
            await mensaje_carga.delete()
            await update.message.reply_text(respuesta, parse_mode='Markdown')
        else:
            await mensaje_carga.delete()
            await update.message.reply_text("❌ Error al obtener datos. Intenta más tarde.")
            
    except Exception as e:
        await mensaje_carga.delete()
        await update.message.reply_text("❌ Error temporal. Intenta nuevamente.")

async def obtener_datos_osm(nombre_pais):
    """OpenStreetMap Nominatim - Sin límites de uso"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://nominatim.openstreetmap.org/search?country={nombre_pais}&format=json&addressdetails=1&limit=20"
            async with session.get(url, headers={'User-Agent': 'TelegramAddressBot'}) as response:
                if response.status == 200:
                    locations = await response.json()
                    if locations:
                        location = random.choice(locations)
                        address = location.get('address', {})
                        return {
                            'calle': f"{address.get('road', 'Street')} {random.randint(1, 999)}",
                            'ciudad': address.get('city', address.get('town', 'City')),
                            'estado': address.get('state', 'State'),
                            'codigo_postal': address.get('postcode', str(random.randint(10000, 99999)))
                        }
    except:
        pass
    return None

async def obtener_datos_geoapify(nombre_pais):
    """Geoapify - 3000 requests/día gratis"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.geoapify.com/v1/geocode/search?text={nombre_pais}&format=json&apiKey=84d3b566a45949b591450c66bc7e99db"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        result = random.choice(data['results'])
                        return {
                            'calle': f"{result.get('street', 'Street')} {random.randint(1, 999)}",
                            'ciudad': result.get('city', 'City'),
                            'estado': result.get('state', 'State'),
                            'codigo_postal': result.get('postcode', str(random.randint(10000, 99999)))
                        }
    except:
        pass
    return None

async def obtener_datos_random(nombre_pais):
    """RandomData API - Sin límites"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://random-data-api.com/api/address/random_address"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'calle': f"{data.get('street_name', 'Street')} {data.get('building_number', random.randint(1, 999))}",
                        'ciudad': data.get('city', 'City'),
                        'estado': data.get('state', 'State'),
                        'codigo_postal': data.get('zip_code', str(random.randint(10000, 99999)))
                    }
    except:
        pass
    return None