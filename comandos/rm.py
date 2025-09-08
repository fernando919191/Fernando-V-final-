import logging
import aiohttp
import random
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Mapeo de códigos de país a nombres completos y códigos telefónicos
PAISES = {
    'mx': {'nombre': 'México', 'codigo': '+52'},
    'col': {'nombre': 'Colombia', 'codigo': '+57'},
    'ven': {'nombre': 'Venezuela', 'codigo': '+58'},
    'us': {'nombre': 'Estados Unidos', 'codigo': '+1'},
    'uk': {'nombre': 'Reino Unido', 'codigo': '+44'},
    'ca': {'nombre': 'Canadá', 'codigo': '+1'},
    'rus': {'nombre': 'Rusia', 'codigo': '+7'},
    'jap': {'nombre': 'Japón', 'codigo': '+81'},
    'chi': {'nombre': 'China', 'codigo': '+86'},
    'hon': {'nombre': 'Honduras', 'codigo': '+504'},
    'chile': {'nombre': 'Chile', 'codigo': '+56'},
    'arg': {'nombre': 'Argentina', 'codigo': '+54'},
    'ind': {'nombre': 'India', 'codigo': '+91'},
    'br': {'nombre': 'Brasil', 'codigo': '+55'},
    'peru': {'nombre': 'Perú', 'codigo': '+51'},
    'es': {'nombre': 'España', 'codigo': '+34'},
    'italia': {'nombre': 'Italia', 'codigo': '+39'},
    'fran': {'nombre': 'Francia', 'codigo': '+33'},
    'suiza': {'nombre': 'Suiza', 'codigo': '+41'}
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
            f"🏙️ **State:** `{datos['estado']}`\n"
            f"📮 **CP:** `{datos['codigo_postal']}`\n"
            f"📞 **Code:** `{pais_info['codigo']}`\n"
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
        # API 1: Nominatim (OpenStreetMap) - Datos reales de ubicaciones
        async with aiohttp.ClientSession() as session:
            # Buscar ubicaciones reales en el país
            url = f"https://nominatim.openstreetmap.org/search?country={nombre_pais}&format=json&limit=10"
            
            async with session.get(url, headers={'User-Agent': 'TelegramBot'}) as response:
                if response.status == 200:
                    locations = await response.json()
                    if locations:
                        # Elegir una ubicación aleatoria
                        location = random.choice(locations)
                        
                        return {
                            'calle': location.get('display_name', '').split(',')[0] if location.get('display_name') else f"Calle {random.randint(1, 1000)}",
                            'estado': location.get('state', 'Estado'),
                            'ciudad': location.get('city', 'Ciudad'),
                            'codigo_postal': location.get('postcode', str(random.randint(10000, 99999))) if location.get('postcode') else str(random.randint(10000, 99999))
                        }
        
        # API 2: Geoapify - Datos más precisos
        async with aiohttp.ClientSession() as session:
            url = f"https://api.geoapify.com/v1/geocode/search?text={nombre_pais}&format=json&apiKey=84d3b566a45949b591450c66bc7e99db"
            # Nota: Necesitarías obtener una API key gratis de geoapify.com
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        result = random.choice(data['results'])
                        return {
                            'calle': result.get('street', f"Calle {random.randint(1, 1000)}"),
                            'estado': result.get('state', 'Estado'),
                            'ciudad': result.get('city', 'Ciudad'),
                            'codigo_postal': result.get('postcode', str(random.randint(10000, 99999)))
                        }
        
        # Si las APIs fallan, generar datos realistas
        return generar_datos_realistas(nombre_pais)
            
    except Exception as e:
        logger.error(f"Error obteniendo datos reales: {e}")
        return generar_datos_realistas(nombre_pais)

def generar_datos_realistas(nombre_pais):
    """Genera datos realistas basados en el país"""
    # Datos realistas por país
    datos_pais = {
        'México': {
            'calles': ['Avenida Reforma', 'Insurgentes Sur', 'Calzada de Tlalpan', 'Paseo de la Reforma', 'Eje Central'],
            'estados': ['CDMX', 'Estado de México', 'Jalisco', 'Nuevo León', 'Puebla'],
            'cps': ['06500', '06600', '44100', '64000', '72000']
        },
        'Colombia': {
            'calles': ['Carrera 7', 'Calle 72', 'Avenida Boyacá', 'Carrera 15', 'Calle 100'],
            'estados': ['Bogotá', 'Antioquia', 'Valle del Cauca', 'Cundinamarca', 'Atlántico'],
            'cps': ['110321', '050001', '760001', '080001', '440001']
        },
        'Estados Unidos': {
            'calles': ['Main Street', 'Broadway', '5th Avenue', 'Sunset Boulevard', 'Michigan Avenue'],
            'estados': ['California', 'New York', 'Texas', 'Florida', 'Illinois'],
            'cps': ['90210', '10001', '77001', '33101', '60601']
        },
        'España': {
            'calles': ['Gran Vía', 'Paseo de Gracia', 'Calle Alcalá', 'Calle Preciados', 'Rambla'],
            'estados': ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao'],
            'cps': ['28001', '08001', '46001', '41001', '48001']
        }
    }
    
    # Datos por defecto si el país no está en la lista
    datos_default = {
        'calles': [f"Calle {random.randint(1, 100)}", f"Avenida {random.randint(1, 100)}"],
        'estados': ['Estado Principal', 'Región Central'],
        'cps': [str(random.randint(10000, 99999))]
    }
    
    pais_data = datos_pais.get(nombre_pais, datos_default)
    
    return {
        'calle': f"{random.choice(pais_data['calles'])} {random.randint(1, 1000)}",
        'estado': random.choice(pais_data['estados']),
        'codigo_postal': random.choice(pais_data['cps'])
    }