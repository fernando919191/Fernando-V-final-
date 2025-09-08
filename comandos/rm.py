from telegram import Update
from telegram.ext import ContextTypes
import aiohttp
import random

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para generar direcciones reales de cualquier país"""
    
    # Mapeo de códigos de país
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
    
    if not context.args:
        # Mostrar lista de países disponibles
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
        await update.message.reply_text(
            "❌ Código de país no válido.\n"
            "Usa /rm sin argumentos para ver la lista de países disponibles."
        )
        return
    
    # Obtener datos del país
    pais_info = PAISES[pais_code]
    
    try:
        # Mostrar mensaje de carga
        mensaje_carga = await update.message.reply_text("🔄 Obteniendo datos en tiempo real...")
        
        # API 1 - OpenStreetMap Nominatim (gratuita)
        async with aiohttp.ClientSession() as session:
            url = f"https://nominatim.openstreetmap.org/search?country={pais_info['nombre']}&format=json&addressdetails=1&limit=20"
            
            async with session.get(url, headers={'User-Agent': 'TelegramBot'}) as response:
                if response.status == 200:
                    locations = await response.json()
                    if locations:
                        # Filtrar ubicaciones con datos completos
                        ubicaciones_validas = [
                            loc for loc in locations 
                            if loc.get('address') and 
                            loc['address'].get('road') and 
                            (loc['address'].get('city') or loc['address'].get('town') or loc['address'].get('village'))
                        ]
                        
                        if ubicaciones_validas:
                            location = random.choice(ubicaciones_validas)
                            address = location['address']
                            
                            calle = f"{address.get('road', 'Calle')} {random.randint(1, 999)}"
                            ciudad = address.get('city', address.get('town', address.get('village', 'Ciudad')))
                            estado = address.get('state', 'Estado')
                            codigo_postal = address.get('postcode', str(random.randint(10000, 99999)))
                            
                            respuesta = f"""
🌍 *Dirección en {pais_info['nombre']}*

🏢 *Calle:* `{calle}`
🏙️ *Ciudad:* `{ciudad}`
🏛️ *Estado:* `{estado}`
📮 *Código Postal:* `{codigo_postal}`
📞 *Código de Teléfono:* `{pais_info['codigo']}`
🇺🇳 *País:* `{pais_info['nombre']}`

✅ *Dirección generada con datos reales*
                            """
                            
                            # Eliminar mensaje de carga y enviar respuesta
                            await mensaje_carga.delete()
                            await update.message.reply_text(respuesta, parse_mode='Markdown')
                            return
        
        # Si la API falla, generar datos realistas
        await mensaje_carga.delete()
        await generar_datos_manuales(update, pais_info)
            
    except Exception as e:
        try:
            await mensaje_carga.delete()
        except:
            pass
        await update.message.reply_text(f"❌ Error al obtener datos: {str(e)}")
        # Intentar con datos manuales como respaldo
        await generar_datos_manuales(update, pais_info)

async def generar_datos_manuales(update: Update, pais_info: dict):
    """Genera datos de dirección realistas para el país"""
    
    # Datos realistas por país
    datos_pais = {
        'México': {
            'calles': ['Avenida Reforma', 'Insurgentes Sur', 'Calzada de Tlalpan', 'Paseo de la Reforma', 'Eje Central'],
            'ciudades': ['Ciudad de México', 'Guadalajara', 'Monterrey', 'Puebla', 'Tijuana'],
            'estados': ['CDMX', 'Jalisco', 'Nuevo León', 'Puebla', 'Baja California'],
            'cps': ['06500', '44100', '64000', '72000', '22000']
        },
        'Colombia': {
            'calles': ['Carrera 7', 'Calle 72', 'Avenida Boyacá', 'Carrera 15', 'Calle 100'],
            'ciudades': ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena'],
            'estados': ['Bogotá D.C.', 'Antioquia', 'Valle del Cauca', 'Atlántico', 'Bolívar'],
            'cps': ['110321', '050001', '760001', '080001', '130001']
        },
        'Estados Unidos': {
            'calles': ['Main Street', 'Broadway', '5th Avenue', 'Sunset Boulevard', 'Michigan Avenue'],
            'ciudades': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
            'estados': ['NY', 'CA', 'IL', 'TX', 'AZ'],
            'cps': ['10001', '90001', '60601', '77001', '85001']
        },
        'España': {
            'calles': ['Gran Vía', 'Paseo de Gracia', 'Calle Alcalá', 'Calle Preciados', 'La Rambla'],
            'ciudades': ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Zaragoza'],
            'estados': ['Madrid', 'Cataluña', 'Valencia', 'Andalucía', 'Aragón'],
            'cps': ['28001', '08001', '46001', '41001', '50001']
        }
    }
    
    # Obtener datos del país o usar valores por defecto
    datos = datos_pais.get(pais_info['nombre'], {
        'calles': [f"Calle Principal {random.randint(1, 100)}"],
        'ciudades': ['Ciudad Capital'],
        'estados': ['Estado Principal'],
        'cps': [str(random.randint(10000, 99999))]
    })
    
    calle = f"{random.choice(datos['calles'])} {random.randint(1, 999)}"
    ciudad = random.choice(datos['ciudades'])
    estado = random.choice(datos['estados'])
    codigo_postal = random.choice(datos['cps'])
    
    respuesta = f"""
🌍 *Dirección en {pais_info['nombre']}*

🏢 *Calle:* `{calle}`
🏙️ *Ciudad:* `{ciudad}`
🏛️ *Estado:* `{estado}`
📮 *Código Postal:* `{codigo_postal}`
📞 *Código de Teléfono:* `{pais_info['codigo']}`
🇺🇳 *País:* `{pais_info['nombre']}`

⚠️ *Datos generados (API no disponible)*
    """
    
    await update.message.reply_text(respuesta, parse_mode='Markdown')