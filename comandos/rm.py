import logging
import aiohttp
import random
import json
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Mapeo de códigos de país a nombres completos y códigos telefónicos
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

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para generar datos de un país específico en tiempo real"""
    try:
        if not context.args:
            # Mostrar lista de países disponibles
            lista_paises = "\n".join([f"• {codigo} - {info['nombre']}" for codigo, info in PAISES.items()])
            await update.message.reply_text(
                f"🌍 *Comando RM - Generador de Datos en Tiempo Real*\n\n"
                f"📝 Uso: `.rm <código_país>`\n\n"
                f"🇺🇳 *Países disponibles:*\n{lista_paises}\n\n"
                f"Ejemplo: `.rm mx` para datos de México",
                parse_mode='Markdown'
            )
            return
        
        pais_code = context.args[0].lower()
        
        if pais_code not in PAISES:
            await update.message.reply_text(
                "❌ Código de país no válido.\n"
                "Usa `.rm` sin argumentos para ver la lista de países disponibles."
            )
            return
        
        # Obtener datos del país en tiempo real
        pais_info = PAISES[pais_code]
        await update.message.reply_text("🔄 Obteniendo datos en tiempo real...")
        
        datos = await obtener_datos_tiempo_real(pais_info['nombre'])
        
        if not datos:
            await update.message.reply_text(
                f"❌ No se pudieron obtener datos en tiempo real para {pais_info['nombre']}.\n"
                "Intenta nuevamente en un momento."
            )
            return
        
        # Construir respuesta formateada con datos copiables
        respuesta = (
            f"🌍 **Datos en tiempo real de {pais_info['nombre']}**\n\n"
            f"🏢 **Street:** `{datos['calle']}`\n"
            f"🏙️ **City:** `{datos['ciudad']}`\n"
            f"🏛️ **State/Region:** `{datos['estado']}`\n"
            f"📮 **ZIP Code:** `{datos['codigo_postal']}`\n"
            f"📞 **Phone Code:** `{pais_info['codigo']}`\n"
            f"🇺🇳 **Country:** `{pais_info['nombre']}`\n\n"
            f"📍 **Coordinates:** {datos['lat']}, {datos['lon']}\n\n"
            f"👤 **By:** {update.effective_user.first_name} [`{update.effective_user.id}`]"
        )
        
        await update.message.reply_text(respuesta, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error en comando rm: {e}")
        await update.message.reply_text("❌ Error al procesar el comando.")

async def obtener_datos_tiempo_real(nombre_pais):
    """Obtiene datos en tiempo real usando múltiples APIs gratuitas"""
    try:
        # 1. Primero intentar con OpenStreetMap Nominatim (gratuito y sin API key)
        async with aiohttp.ClientSession() as session:
            # Buscar ubicaciones reales en el país
            url = f"https://nominatim.openstreetmap.org/search?country={nombre_pais}&format=json&addressdetails=1&limit=20"
            
            async with session.get(url, headers={'User-Agent': 'TelegramBot/1.0'}) as response:
                if response.status == 200:
                    locations = await response.json()
                    if locations:
                        # Filtrar solo resultados con dirección completa
                        ubicaciones_validas = [
                            loc for loc in locations 
                            if loc.get('address') and 
                            loc['address'].get('road') and 
                            loc['address'].get('city') and
                            loc['address'].get('state') and
                            loc['address'].get('postcode')
                        ]
                        
                        if ubicaciones_validas:
                            location = random.choice(ubicaciones_validas)
                            address = location['address']
                            
                            return {
                                'calle': f"{address.get('road', 'Street')} {random.randint(1, 999)}",
                                'ciudad': address.get('city', address.get('town', address.get('village', 'City'))),
                                'estado': address.get('state', 'State'),
                                'codigo_postal': address.get('postcode', str(random.randint(10000, 99999))),
                                'lat': location.get('lat', '0'),
                                'lon': location.get('lon', '0')
                            }
        
        # 2. Si Nominatim no devuelve resultados, usar API de ciudades aleatorias
        async with aiohttp.ClientSession() as session:
            # Obtener una ciudad aleatoria del país
            url = f"https://api.teleport.org/api/countries/iso_alpha2:{obtener_codigo_iso(nombre_pais)}/cities/"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('_embedded') and data['_embedded'].get('city:search-results'):
                        ciudades = data['_embedded']['city:search-results']
                        if ciudades:
                            ciudad = random.choice(ciudades)
                            nombre_ciudad = ciudad['matching_full_name'].split(',')[0]
                            
                            # Ahora obtener detalles de esa ciudad
                            ciudad_url = ciudad['_links']['city:item']['href']
                            async with session.get(ciudad_url) as ciudad_response:
                                if ciudad_response.status == 200:
                                    ciudad_data = await ciudad_response.json()
                                    ubicacion = ciudad_data.get('location', {})
                                    
                                    return {
                                        'calle': f"{generar_nombre_calle()} {random.randint(1, 999)}",
                                        'ciudad': nombre_ciudad,
                                        'estado': ubicacion.get('region', {}).get('name', 'State'),
                                        'codigo_postal': generar_codigo_postal(nombre_pais),
                                        'lat': ubicacion.get('latlon', {}).get('latitude', '0'),
                                        'lon': ubicacion.get('latlon', {}).get('longitude', '0')
                                    }
        
        # 3. Como último recurso, usar una API de direcciones aleatorias
        async with aiohttp.ClientSession() as session:
            # Esta API genera direcciones aleatorias pero realistas
            url = f"https://random-data-api.com/api/address/random_address?size=1"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return {
                            'calle': f"{data.get('street_name', 'Street')} {data.get('building_number', random.randint(1, 999))}",
                            'ciudad': data.get('city', 'City'),
                            'estado': data.get('state', 'State'),
                            'codigo_postal': data.get('zip_code', str(random.randint(10000, 99999))),
                            'lat': '0',
                            'lon': '0'
                        }
        
        return None
            
    except Exception as e:
        logger.error(f"Error obteniendo datos en tiempo real: {e}")
        return None

def obtener_codigo_iso(nombre_pais):
    """Convierte nombre del país a código ISO alpha2"""
    codigos = {
        'United States': 'US', 'Mexico': 'MX', 'Colombia': 'CO', 'Venezuela': 'VE',
        'United Kingdom': 'GB', 'Canada': 'CA', 'Russia': 'RU', 'Japan': 'JP',
        'China': 'CN', 'Honduras': 'HN', 'Chile': 'CL', 'Argentina': 'AR',
        'India': 'IN', 'Brazil': 'BR', 'Peru': 'PE', 'Spain': 'ES',
        'Italy': 'IT', 'France': 'FR', 'Switzerland': 'CH'
    }
    return codigos.get(nombre_pais, 'US')

def generar_nombre_calle():
    """Genera nombres de calles realistas"""
    prefijos = ['Main', 'Oak', 'Maple', 'Cedar', 'Pine', 'Elm', 'Washington', 'Lincoln', 'Jefferson', 'Park']
    sufijos = ['St', 'Ave', 'Blvd', 'Rd', 'Ln', 'Dr', 'Ct', 'Pl']
    return f"{random.choice(prefijos)} {random.choice(sufijos)}"

def generar_codigo_postal(nombre_pais):
    """Genera códigos postales realistas según el país"""
    formatos = {
        'United States': lambda: str(random.randint(10000, 99999)),
        'Mexico': lambda: str(random.randint(10000, 99999)),
        'Canada': lambda: f"{random.choice('ABCEGHJKLMNPRSTVXY')}{random.randint(0,9)}{random.choice('ABCEGHJKLMNPRSTVWXYZ')} {random.randint(0,9)}{random.choice('ABCEGHJKLMNPRSTVWXYZ')}{random.randint(0,9)}"),
        'United Kingdom': lambda: f"{random.choice('ABCDEFGHIJKLMNOPRSTUWYZ')}{random.choice('ABCDEFGHKLMNOPQRSTUVWXY')}{random.randint(1,99)} {random.randint(1,99)}{random.choice('ABCDEFGHJKPMNW')}{random.choice('ABCDEFGHJKSTUW')}"),
    }
    return formatos.get(nombre_pais, lambda: str(random.randint(10000, 99999)))()