import logging
import aiohttp
import random
import os
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Configuración de API Keys
POSITIONSTACK_API_KEY = os.getenv('POSITIONSTACK_API_KEY', '48e852770cd54849c5e87fbc62326652')  # Reemplaza con tu API Key

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
    """Obtiene datos REALES usando PositionStack API"""
    try:
        # 1. Primero intentar con PositionStack (más confiable)
        async with aiohttp.ClientSession() as session:
            # Buscar ciudades en el país
            query = random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
                                  'Miami', 'Dallas', 'Seattle', 'Boston', 'Atlanta']) if nombre_pais == 'United States' else nombre_pais
            
            url = f"http://api.positionstack.com/v1/forward?access_key={POSITIONSTACK_API_KEY}&query={query}&country={nombre_pais}&limit=10"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data'):
                        # Filtrar resultados que tengan datos completos
                        resultados_validos = [r for r in data['data'] 
                                            if r.get('street') and r.get('locality') and r.get('region')]
                        
                        if resultados_validos:
                            result = random.choice(resultados_validos)
                            return {
                                'calle': result.get('street', 'Main Street'),
                                'ciudad': result.get('locality', 'City'),
                                'estado': result.get('region', 'State'),
                                'codigo_postal': result.get('postal_code', str(random.randint(10000, 99999)))
                            }
        
        # 2. Si PositionStack falla, usar datos predefinidos de alta calidad
        return generar_datos_realistas(nombre_pais)
            
    except Exception as e:
        logger.error(f"Error obteniendo datos reales: {e}")
        return generar_datos_realistas(nombre_pais)

def generar_datos_realistas(nombre_pais):
    """Genera datos realistas basados en el país con información más específica"""
    # Base de datos mejorada con datos reales de calles, ciudades y códigos postales
    datos_pais = {
        'United States': {
            'calles': ['Main Street', 'Broadway', '5th Avenue', 'Park Avenue', 'Sunset Boulevard', 
                      'Michigan Avenue', 'Market Street', 'Peachtree Street', 'Bourbon Street', 'Lombard Street'],
            'ciudades': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
                        'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'],
            'estados': ['New York', 'California', 'Illinois', 'Texas', 'Arizona', 
                       'Pennsylvania', 'Florida', 'Ohio', 'Georgia', 'North Carolina'],
            'cps': ['10001', '90001', '60601', '77001', '85001', 
                   '19101', '33101', '43201', '30301', '28201']
        },
        'Mexico': {
            'calles': ['Avenida Reforma', 'Insurgentes Sur', 'Paseo de la Reforma', 'Avenida Juárez', 
                      'Calzada de Tlalpan', 'Eje Central', 'Avenida de los Insurgentes', 'Avenida Hidalgo', 
                      'Avenida Chapultepec', 'Avenida Patriotismo'],
            'ciudades': ['Mexico City', 'Guadalajara', 'Monterrey', 'Puebla', 'Tijuana', 
                        'León', 'Ciudad Juárez', 'Torreón', 'Querétaro', 'Merida'],
            'estados': ['Ciudad de México', 'Jalisco', 'Nuevo León', 'Puebla', 'Baja California', 
                       'Guanajuato', 'Chihuahua', 'Coahuila', 'Querétaro', 'Yucatán'],
            'cps': ['06500', '44100', '64000', '72000', '22000', 
                   '37000', '32000', '27000', '76000', '97000']
        },
        'Colombia': {
            'calles': ['Carrera 7', 'Calle 72', 'Avenida Boyacá', 'Carrera 15', 'Calle 100', 
                      'Avenida El Dorado', 'Carrera 50', 'Avenida Las Américas', 'Carrera 13', 'Calle 26'],
            'ciudades': ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 
                        'Cúcuta', 'Bucaramanga', 'Pereira', 'Santa Marta', 'Ibagué'],
            'estados': ['Bogotá D.C.', 'Antioquia', 'Valle del Cauca', 'Atlántico', 'Bolívar', 
                       'Norte de Santander', 'Santander', 'Risaralda', 'Magdalena', 'Tolima'],
            'cps': ['110321', '050001', '760001', '080001', '130001', 
                   '540001', '680001', '660001', '470001', '730001']
        },
        'Spain': {
            'calles': ['Gran Vía', 'Paseo de Gracia', 'Calle Alcalá', 'Calle Preciados', 'La Rambla', 
                      'Calle Mayor', 'Paseo de la Castellana', 'Calle Serrano', 'Calle Atocha', 'Calle Fuencarral'],
            'ciudades': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Zaragoza', 
                        'Málaga', 'Murcia', 'Palma', 'Las Palmas', 'Bilbao'],
            'estados': ['Madrid', 'Catalonia', 'Valencia', 'Andalusia', 'Aragon', 
                       'Region of Murcia', 'Balearic Islands', 'Canary Islands', 'Basque Country'],
            'cps': ['28001', '08001', '46001', '41001', '50001', 
                   '29001', '30001', '07001', '35001', '48001']
        }
    }
    
    # Datos por defecto si el país no está en la lista
    datos_default = {
        'calles': [f"Street {random.randint(1, 100)}", f"Avenue {random.randint(1, 100)}"],
        'ciudades': ['Capital City', 'Main City'],
        'estados': ['Main State', 'Central Region'],
        'cps': [str(random.randint(10000, 99999))]
    }
    
    # Buscar coincidencia
    pais_data = datos_pais.get(nombre_pais, datos_default)
    
    return {
        'calle': f"{random.choice(pais_data['calles'])} {random.randint(1, 1000)}",
        'ciudad': random.choice(pais_data['ciudades']),
        'estado': random.choice(pais_data['estados']),
        'codigo_postal': random.choice(pais_data['cps'])
    }