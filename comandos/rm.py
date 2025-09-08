import logging
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.usuarios import obtener_usuario_por_id
from index import es_administrador

logger = logging.getLogger(__name__)

# Mapeo de códigos de país a nombres completos
PAISES = {
    'mx': 'México', 'col': 'Colombia', 'ven': 'Venezuela', 'us': 'Estados Unidos',
    'uk': 'Reino Unido', 'ca': 'Canadá', 'rus': 'Rusia', 'jap': 'Japón',
    'chi': 'China', 'hon': 'Honduras', 'chile': 'Chile', 'arg': 'Argentina',
    'ind': 'India', 'br': 'Brasil', 'peru': 'Perú', 'es': 'España',
    'italia': 'Italia', 'fran': 'Francia', 'suiza': 'Suiza'
}

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para generar datos de un país específico"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if not context.args:
            # Mostrar lista de países disponibles
            lista_paises = "\n".join([f"• {codigo} - {nombre}" for codigo, nombre in PAISES.items()])
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
        pais_nombre = PAISES[pais_code]
        datos = await obtener_datos_pais(pais_code)
        
        if not datos:
            await update.message.reply_text(
                f"❌ No se pudieron obtener datos para {pais_nombre}.\n"
                "Intenta nuevamente más tarde."
            )
            return
        
        # Construir respuesta formateada
        respuesta = (
            f"🌍 **Datos de {pais_nombre}**\n\n"
            f"🏢 **Street:** {datos['street']}\n"
            f"🏙️ **State:** {datos['state']}\n"
            f"📮 **CP:** {datos['postcode']}\n"
            f"🔢 **Number:** {datos['number']}\n"
            f"🇺🇳 **Country:** {pais_nombre}\n\n"
            f"👤 **By:** {update.effective_user.first_name} [{user_id}]"
        )
        
        await update.message.reply_text(respuesta, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error en comando rm: {e}")
        await update.message.reply_text("❌ Error al procesar el comando.")

async def obtener_datos_pais(codigo_pais):
    """Obtiene datos aleatorios de una API para el país especificado"""
    try:
        async with aiohttp.ClientSession() as session:
            # API 1: RandomUser API (funciona para muchos países)
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
                            'number': location['street']['number'],
                            'city': location['city'],
                            'country': location['country']
                        }
            
            # Si la primera API falla, intentar con API alternativa
            url_alt = "https://random-data-api.com/api/address/random_address"
            async with session.get(url_alt, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'street': data['street_address'],
                        'state': data['state'],
                        'postcode': data['zip_code'],
                        'number': data['building_number'],
                        'city': data['city'],
                        'country': data['country']
                    }
            
            return None
            
    except Exception as e:
        logger.error(f"Error obteniendo datos de país {codigo_pais}: {e}")
        return None

# Función alternativa para países específicos con datos predefinidos
def datos_predefinidos_pais(codigo_pais):
    """Datos predefinidos para cuando la API falle"""
    datos_base = {
        'street': "Calle Principal 123",
        'state': "Estado",
        'postcode': "12345",
        'number': "123",
        'city': "Ciudad Capital",
        'country': PAISES.get(codigo_pais, "País")
    }
    
    # Personalizar por país
    personalizaciones = {
        'mx': {'postcode': "06700", 'state': "Ciudad de México"},
        'us': {'postcode': "10001", 'state': "New York"},
        'es': {'postcode': "28001", 'state': "Madrid"},
        'arg': {'postcode': "C1002", 'state': "Buenos Aires"},
        'col': {'postcode': "110011", 'state': "Bogotá"},
        'ven': {'postcode': "1010", 'state': "Caracas"}
    }
    
    if codigo_pais in personalizaciones:
        datos_base.update(personalizaciones[codigo_pais])
    
    return datos_base