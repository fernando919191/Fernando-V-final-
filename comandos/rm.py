import logging
import aiohttp
import random
import os
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Configuración de la API Key
GEOAPIFY_API_KEY = os.getenv('GEOAPIFY_API_KEY', '84d3b566a45949b591450c66bc7e99db')

# Mapeo de códigos de país a nombres completos y códigos telefónicos
PAISES = {
    'mx': {'nombre': 'México', 'codigo': '+52'},
    'col': {'nombre': 'Colombia', 'codigo': '+57'},
    'ven': {'nombre': 'Venezuela', 'codigo': '+58'},
    'us': {'nombre': 'United States', 'codigo': '+1'},  # Cambiado a inglés para la API
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
    """Comando para generar datos de un país específico"""
    try:
        if not context.args:
            # Mostrar lista de países disponibles
            lista_paises = "\n".join([f"• {codigo} - {info['nombre']}" for codigo, info in PAISES.items()])
            await update.message.reply_text(
                f"🌍 *Comando RM - Generador de Datos*\n\n"
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
        
        # Obtener datos del país
        pais_info = PAISES[pais_code]
        datos = await obtener_datos_reales_pais(pais_info['nombre'])
        
        if not datos:
            await update.message.reply_text(
                f"❌ No se pudieron obtener datos para {pais_info['nombre']}.\n"
                "Intenta nuevamente más tarde."
            )
            return
        
        # Construir respuesta formateada con datos copiables
        respuesta = (
            f"🌍 **Datos de {pais_info['nombre']}**\n\n"
            f"🏢 **Street:** `{datos['calle']}`\n"
            f"🏙️ **City:** `{datos['ciudad']}`\n"
            f"🏛️ **State:** `{datos['estado']}`\n"
            f"📮 **ZIP Code:** `{datos['codigo_postal']}`\n"
            f"📞 **Phone Code:** `{pais_info['codigo']}`\n"
            f"🇺🇳 **Country:** `{pais_info['nombre']}`\n\n"
            f"👤 **By:** {update.effective_user.first_name} [`{update.effective_user.id}`]"
        )
        
        await update.message.reply_text(respuesta, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error en comando rm: {e}")
        await update.message.reply_text("❌ Error al procesar el comando.")

async def obtener_datos_reales_pais(nombre_pais):
    """Obtiene datos REALES y NUEVOS usando APIs de geolocalización"""
    try:
        # 1. Primero intentar con Geoapify (más confiable)
        async with aiohttp.ClientSession() as session:
            url = f"https://api.geoapify.com/v1/geocode/search?country={nombre_pais}&format=json&limit=20&apiKey={GEOAPIFY_API_KEY}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        # Filtrar resultados que tengan calle y ciudad
                        resultados_validos = [r for r in data['results'] if r.get('street') and r.get('city')]
                        if resultados_validos:
                            result = random.choice(resultados_validos)
                            return {
                                'calle': result.get('street', 'Main Street'),
                                'estado': result.get('state', 'State'),
                                'ciudad': result.get('city', 'City'),
                                'codigo_postal': result.get('postcode', str(random.randint(10000, 99999)))
                            }
        
        # 2. Si Geoapify falla, intentar con Nominatim
        async with aiohttp.ClientSession() as session:
            # Buscar ubicaciones reales en el país
            url = f"https://nominatim.openstreetmap.org/search?country={nombre_pais}&format=json&limit=20"
            
            async with session.get(url, headers={'User-Agent': 'TelegramBot'}) as response:
                if response.status == 200:
                    locations = await response.json()
                    if locations:
                        # Elegir una ubicación aleatoria
                        location = random.choice(locations)
                        display_name = location.get('display_name', '')
                        address_parts = display_name.split(',')
                        
                        return {
                            'calle': address_parts[0] if len(address_parts) > 0 else f"Street {random.randint(1, 1000)}",
                            'estado': location.get('state', 'State'),
                            'ciudad': location.get('city', 'City'),
                            'codigo_postal': location.get('postcode', str(random.randint(10000, 99999)))
                        }
        
        # 3. Si ambas APIs fallan, generar datos realistas
        return generar_datos_realistas(nombre_pais)
            
    except Exception as e:
        logger.error(f"Error obteniendo datos reales: {e}")
        return generar_datos_realistas(nombre_pais)

def generar_datos_realistas(nombre_pais):
    """Genera datos realistas basados en el país"""
    # Datos realistas por país (en inglés para coincidir con los nombres de la API)
    datos_pais = {
        'United States': {
            'calles': ['Main Street', 'Broadway', '5th Avenue', 'Sunset Boulevard', 'Michigan Avenue'],
            'ciudades': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
            'estados': ['California', 'New York', 'Texas', 'Florida', 'Illinois'],
            'cps': ['90210', '10001', '77001', '33101', '60601']
        },
        'México': {
            'calles': ['Avenida Reforma', 'Insurgentes Sur', 'Calzada de Tlalpan', 'Paseo de la Reforma', 'Eje Central'],
            'ciudades': ['Ciudad de México', 'Guadalajara', 'Monterrey', 'Puebla', 'Tijuana'],
            'estados': ['CDMX', 'Estado de México', 'Jalisco', 'Nuevo León', 'Puebla'],
            'cps': ['06500', '06600', '44100', '64000', '72000']
        },
        'Colombia': {
            'calles': ['Carrera 7', 'Calle 72', 'Avenida Boyacá', 'Carrera 15', 'Calle 100'],
            'ciudades': ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena'],
            'estados': ['Bogotá D.C.', 'Antioquia', 'Valle del Cauca', 'Atlántico', 'Bolívar'],
            'cps': ['110321', '050001', '760001', '080001', '130001']
        }
    }
    
    # Datos por defecto si el país no está en la lista
    datos_default = {
        'calles': [f"Street {random.randint(1, 100)}", f"Avenue {random.randint(1, 100)}"],
        'ciudades': ['Capital City', 'Main City'],
        'estados': ['Main State', 'Central Region'],
        'cps': [str(random.randint(10000, 99999))]
    }
    
    # Buscar coincidencia (incluyendo nombres en español)
    nombres_alternativos = {
        'United States': 'Estados Unidos',
        'México': 'Mexico',
        'Colombia': 'Colombia'
    }
    
    # Verificar si el país está en nuestros datos
    pais_data = None
    for nombre, datos in datos_pais.items():
        if nombre.lower() == nombre_pais.lower() or nombres_alternativos.get(nombre, '').lower() == nombre_pais.lower():
            pais_data = datos
            break
    
    if not pais_data:
        pais_data = datos_default
    
    return {
        'calle': f"{random.choice(pais_data['calles'])} {random.randint(1, 1000)}",
        'ciudad': random.choice(pais_data['ciudades']),
        'estado': random.choice(pais_data['estados']),
        'codigo_postal': random.choice(pais_data['cps'])
    }