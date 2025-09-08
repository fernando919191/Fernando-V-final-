import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_usuario_por_id
from index import es_administrador

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
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
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
        datos = await obtener_datos_pais(pais_code)
        
        if not datos:
            await update.message.reply_text(
                f"❌ No se pudieron obtener datos para {pais_info['nombre']}.\n"
                "Intenta nuevamente más tarde."
            )
            return
        
        # Construir respuesta formateada con datos copiables
        respuesta = (
            f"🌍 **Datos de {pais_info['nombre']}**\n\n"
            f"🏢 **Street:** `{datos['street']}`\n"
            f"🏙️ **State:** `{datos['state']}`\n"
            f"📮 **CP:** `{datos['postcode']}`\n"
            f"📞 **Code:** `{pais_info['codigo']}`\n"
            f"🇺🇳 **Country:** `{pais_info['nombre']}`\n\n"
            f"👤 **By:** {update.effective_user.first_name} [`{user_id}`]"
        )
        
        await update.message.reply_text(respuesta, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error en comando rm: {e}")
        await update.message.reply_text("❌ Error al procesar el comando.")

async def obtener_datos_pais(codigo_pais):
    """Obtiene datos aleatorios de una API para el país especificado"""
    try:
        async with aiohttp.ClientSession() as session:
            # API de RandomUser
            url = f"https://randomuser.me/api/?nat={codigo_pais}"
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['results']:
                        user = data['results'][0]
                        location = user['location']
                        
                        return {
                            'street': f"{location['street']['name']} {location['street']['number']}",
                            'state': location['state'],
                            'postcode': str(location['postcode']),
                            'city': location['city']
                        }
            
            # Si falla, usar datos predefinidos
            return datos_predefinidos_pais(codigo_pais)
            
    except Exception:
        # Fallback a datos predefinidos en caso de error
        return datos_predefinidos_pais(codigo_pais)

def datos_predefinidos_pais(codigo_pais):
    """Datos predefinidos para cuando la API falle"""
    pais_info = PAISES.get(codigo_pais, {'nombre': 'País', 'codigo': '+00'})
    
    datos_base = {
        'street': "Calle Principal 123",
        'state': "Estado",
        'postcode': "12345",
        'city': "Ciudad Capital"
    }
    
    # Personalizar por país
    personalizaciones = {
        'mx': {'street': "Avenida Reforma 456", 'state': "CDMX", 'postcode': "06500", 'city': "Ciudad de México"},
        'us': {'street': "Broadway 789", 'state': "NY", 'postcode': "10001", 'city': "New York"},
        'es': {'street': "Gran Vía 101", 'state': "Madrid", 'postcode': "28013", 'city': "Madrid"},
        'arg': {'street': "Avenida 9 de Julio 1000", 'state': "CABA", 'postcode': "C1073", 'city': "Buenos Aires"},
        'col': {'street': "Carrera 7 #71-52", 'state': "Bogotá", 'postcode': "110321", 'city': "Bogotá"},
        'ven': {'street': "Avenida Bolívar 123", 'state': "Caracas", 'postcode': "1010", 'city': "Caracas"},
        'br': {'street': "Avenida Paulista 1000", 'state': "SP", 'postcode': "01310", 'city': "São Paulo"},
        'chi': {'street': "Avenida Providencia 1234", 'state': "RM", 'postcode': "750000", 'city': "Santiago"},
        'fr': {'street': "Champs-Élysées 56", 'state': "Île-de-France", 'postcode': "75008", 'city': "Paris"},
        'uk': {'street': "Oxford Street 123", 'state': "London", 'postcode': "W1D 1BS", 'city': "London"},
        'jap': {'street': "Shibuya Crossing 1", 'state': "Tokyo", 'postcode': "150-0043", 'city': "Tokyo"}
    }
    
    if codigo_pais in personalizaciones:
        datos_base.update(personalizaciones[codigo_pais])
    
    return datos_base