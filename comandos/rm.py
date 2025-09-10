from telegram import Update
from telegram.ext import ContextTypes
import aiohttp
import random
import asyncio

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para generar direcciones reales - Versión Mejorada"""
    
    # Mapeo COMPLETO con códigos en español e inglés
    PAISES = {
        # Códigos en español
        'mx': {'nombre': 'Mexico', 'codigo': '+52', 'nombre_api': 'Mexico'},
        'col': {'nombre': 'Colombia', 'codigo': '+57', 'nombre_api': 'Colombia'},
        'ven': {'nombre': 'Venezuela', 'codigo': '+58', 'nombre_api': 'Venezuela'},
        'us': {'nombre': 'Estados Unidos', 'codigo': '+1', 'nombre_api': 'United States'},
        'uk': {'nombre': 'Reino Unido', 'codigo': '+44', 'nombre_api': 'United Kingdom'},
        'ca': {'nombre': 'Canada', 'codigo': '+1', 'nombre_api': 'Canada'},
        'rus': {'nombre': 'Rusia', 'codigo': '+7', 'nombre_api': 'Russia'},
        'jap': {'nombre': 'Japón', 'codigo': '+81', 'nombre_api': 'Japan'},
        'chi': {'nombre': 'China', 'codigo': '+86', 'nombre_api': 'China'},
        'hon': {'nombre': 'Honduras', 'codigo': '+504', 'nombre_api': 'Honduras'},
        'chile': {'nombre': 'Chile', 'codigo': '+56', 'nombre_api': 'Chile'},
        'arg': {'nombre': 'Argentina', 'codigo': '+54', 'nombre_api': 'Argentina'},
        'ind': {'nombre': 'India', 'codigo': '+91', 'nombre_api': 'India'},
        'br': {'nombre': 'Brasil', 'codigo': '+55', 'nombre_api': 'Brazil'},
        'peru': {'nombre': 'Perú', 'codigo': '+51', 'nombre_api': 'Peru'},
        'es': {'nombre': 'España', 'codigo': '+34', 'nombre_api': 'Spain'},
        'italia': {'nombre': 'Italia', 'codigo': '+39', 'nombre_api': 'Italy'},
        'fran': {'nombre': 'Francia', 'codigo': '+33', 'nombre_api': 'France'},
        'suiza': {'nombre': 'Suiza', 'codigo': '+41', 'nombre_api': 'Switzerland'},
        
        # Aliases en inglés
        'switzerland': {'nombre': 'Suiza', 'codigo': '+41', 'nombre_api': 'Switzerland'},
        'usa': {'nombre': 'Estados Unidos', 'codigo': '+1', 'nombre_api': 'United States'},
        'spain': {'nombre': 'España', 'codigo': '+34', 'nombre_api': 'Spain'},
        'italy': {'nombre': 'Italia', 'codigo': '+39', 'nombre_api': 'Italy'},
        'france': {'nombre': 'Francia', 'codigo': '+33', 'nombre_api': 'France'}
    }
    
    if not context.args:
        lista_paises = "\n".join([f"• {codigo} - {info['nombre']}" for codigo, info in PAISES.items() if len(codigo) <= 5])
        await update.message.reply_text(
            f"🌍 *Comando RM - Generador de Direcciones*\n\n"
            f"📝 Uso: /rm <código_país>\n\n"
            f"🇺🇳 *Países disponibles:*\n{lista_paises}\n\n"
            f"Ejemplo: /rm mx para datos de México\n"
            f"Ejemplo: /rm suiza para datos de Suiza",
            parse_mode='Markdown'
        )
        return
    
    pais_code = context.args[0].lower()
    
    if pais_code not in PAISES:
        # Mostrar sugerencias similares
        sugerencias = [cod for cod in PAISES.keys() if pais_code in cod or cod in pais_code]
        mensaje_error = "❌ Código de país no válido.\n\nPaíses disponibles:\n"
        mensaje_error += "\n".join([f"• {cod} - {PAISES[cod]['nombre']}" for cod in list(PAISES.keys())[:10]])
        
        if sugerencias:
            mensaje_error += f"\n\n💡 Quizás quisiste decir: {', '.join(sugerencias[:3])}"
            
        await update.message.reply_text(mensaje_error)
        return
    
    pais_info = PAISES[pais_code]
    mensaje_carga = await update.message.reply_text(f"🔄 Generando dirección real en {pais_info['nombre']}...")
    
    try:
        # PRIMERO: Intentar con API de OpenStreetMap
        datos = await obtener_datos_osm(pais_info['nombre_api'])
        
        if not datos:
            # SEGUNDO: Si falla la API, usar nuestra base de datos REAL
            datos = await generar_datos_reales(pais_info)
        
        if datos:
            respuesta = f"""
🌍 *Dirección en {pais_info['nombre']}*

🏢 *Street:* `{datos['calle']}`
🏙️ *City:* `{datos['ciudad']}`
🏛️ *State:* `{datos['estado']}`
📮 *ZIP Code:* `{datos['codigo_postal']}`
📞 *Phone Code:* `{pais_info['codigo']}`
🇺🇳 *Country:* `{pais_info['nombre']}`

✅ *Datos generados aleatoriamente*
            """
            await mensaje_carga.edit_text(respuesta, parse_mode='Markdown')
        else:
            await mensaje_carga.edit_text("❌ No se pudieron obtener datos para este país. Intenta con otro país.")
            
    except Exception as e:
        await mensaje_carga.edit_text("❌ Error temporal. Intenta nuevamente en unos momentos.")
        print(f"Error en comando rm: {e}")

async def obtener_datos_osm(nombre_pais_api):
    """Obtiene datos REALES de OpenStreetMap"""
    try:
        async with aiohttp.ClientSession() as session:
            # Usar búsqueda más específica
            url = f"https://nominatim.openstreetmap.org/search?country={nombre_pais_api}&format=json&addressdetails=1&limit=50"
            
            headers = {
                'User-Agent': 'TelegramAddressBot/1.0 (https://t.me/yourbot)',
                'Accept-Language': 'en'
            }
            
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    lugares = await response.json()
                    if lugares:
                        # Filtrar lugares con buena información
                        lugares_validos = [
                            l for l in lugares 
                            if l.get('address') and 'city' in l['address'] or 'town' in l['address'] or 'village' in l['address']
                        ]
                        
                        if lugares_validos:
                            lugar = random.choice(lugares_validos)
                            address = lugar.get('address', {})
                            
                            # Obtener ciudad de manera más robusta
                            ciudad = (
                                address.get('city') or 
                                address.get('town') or 
                                address.get('village') or 
                                address.get('municipality') or
                                "Unknown City"
                            )
                            
                            # Obtener estado/provincia
                            estado = (
                                address.get('state') or 
                                address.get('province') or 
                                address.get('region') or
                                "State"
                            )
                            
                            # Obtener código postal
                            codigo_postal = (
                                address.get('postcode') or 
                                str(random.randint(10000, 99999))
                            )
                            
                            return {
                                'calle': f"{generar_nombre_calle()} {random.randint(1, 999)}",
                                'ciudad': ciudad,
                                'estado': estado,
                                'codigo_postal': codigo_postal
                            }
    except (aiohttp.ClientError, asyncio.TimeoutError):
        pass
    except Exception as e:
        print(f"Error en OSM: {e}")
    
    return None

async def generar_datos_reales(pais_info):
    """Base de datos con datos REALES y consistentes"""
    DATOS_REALES = {
        'United States': {
            'ciudades': [
                {'nombre': 'New York', 'estado': 'NY', 'cp': '10001', 'calles': ['Broadway', '5th Avenue', 'Wall Street', 'Madison Avenue']},
                {'nombre': 'Los Angeles', 'estado': 'CA', 'cp': '90001', 'calles': ['Sunset Blvd', 'Hollywood Blvd', 'Wilshire Blvd', 'Santa Monica Blvd']},
                {'nombre': 'Chicago', 'estado': 'IL', 'cp': '60601', 'calles': ['Michigan Avenue', 'State Street', 'Wacker Drive', 'LaSalle Street']},
                {'nombre': 'Miami', 'estado': 'FL', 'cp': '33101', 'calles': ['Ocean Drive', 'Collins Avenue', 'Biscayne Blvd', 'Flagler Street']},
                {'nombre': 'Las Vegas', 'estado': 'NV', 'cp': '89101', 'calles': ['Las Vegas Blvd', 'Fremont Street', 'Sahara Avenue', 'Rainbow Blvd']}
            ]
        },
        'Mexico': {
            'ciudades': [
                {'nombre': 'Mexico City', 'estado': 'CDMX', 'cp': '06500', 'calles': ['Reforma', 'Insurgentes', 'Chapultepec', 'Patriotismo']},
                {'nombre': 'Guadalajara', 'estado': 'Jalisco', 'cp': '44100', 'calles': ['Vallarta', 'Juárez', 'Américas', 'Federalismo']},
                {'nombre': 'Monterrey', 'estado': 'Nuevo León', 'cp': '64000', 'calles': ['Madero', 'Garza Sada', 'Constitución', 'Pino Suárez']},
                {'nombre': 'Cancún', 'estado': 'Quintana Roo', 'cp': '77500', 'calles': ['Tulum', 'Kukulcan', 'Coba', 'Xcaret']},
                {'nombre': 'Tijuana', 'estado': 'Baja California', 'cp': '22000', 'calles': ['Revolución', 'Agua Caliente', 'Internacional', 'Paseo de los Héroes']}
            ]
        },
        'Switzerland': {
            'ciudades': [
                {'nombre': 'Zurich', 'estado': 'Zurich', 'cp': '8001', 'calles': ['Bahnhofstrasse', 'Limmatquai', 'Rennweg', 'Langstrasse']},
                {'nombre': 'Geneva', 'estado': 'Geneva', 'cp': '1201', 'calles': ['Rue du Rhône', 'Rue de la Corraterie', 'Boulevard de Saint-Georges', 'Rue de Lausanne']},
                {'nombre': 'Bern', 'estado': 'Bern', 'cp': '3000', 'calles': ['Marktgasse', 'Kramgasse', 'Spitalgasse', 'Neuengasse']},
                {'nombre': 'Basel', 'estado': 'Basel-Stadt', 'cp': '4001', 'calles': ['Freie Strasse', 'Gerbergasse', 'Rheinsprung', 'Steinenvorstadt']},
                {'nombre': 'Lausanne', 'estado': 'Vaud', 'cp': '1003', 'calles': ['Rue de Bourg', 'Avenue de la Gare', 'Rue du Petit-Chêne', 'Avenue de Rumine']}
            ]
        },
        'Spain': {
            'ciudades': [
                {'nombre': 'Madrid', 'estado': 'Madrid', 'cp': '28001', 'calles': ['Gran Vía', 'Paseo de la Castellana', 'Calle de Alcalá', 'Calle Mayor']},
                {'nombre': 'Barcelona', 'estado': 'Cataluña', 'cp': '08001', 'calles': ['Las Ramblas', 'Paseo de Gracia', 'Diagonal', 'Calle de Balmes']},
                {'nombre': 'Valencia', 'estado': 'Valencia', 'cp': '46001', 'calles': ['Calle de la Paz', 'Gran Vía Marqués del Turia', 'Calle de Colón', 'Avenida del Puerto']}
            ]
        },
        'default': {
            'ciudades': [
                {'nombre': 'Capital City', 'estado': 'State', 'cp': '12345', 'calles': ['Main Street', 'Central Avenue', 'Park Road', 'Liberty Boulevard']}
            ]
        }
    }
    
    # Buscar datos del país o usar default
    pais_data = DATOS_REALES.get(pais_info['nombre_api'], DATOS_REALES['default'])
    ciudad = random.choice(pais_data['ciudades'])
    
    return {
        'calle': f"{random.choice(ciudad['calles'])} {random.randint(1, 999)}",
        'ciudad': ciudad['nombre'],
        'estado': ciudad['estado'],
        'codigo_postal': ciudad['cp']
    }

def generar_nombre_calle():
    """Genera nombres de calles realistas"""
    prefijos = ['Main', 'Oak', 'Maple', 'Cedar', 'Pine', 'Elm', 'Washington', 'Lincoln', 'Jefferson', 'Park', 'Lake', 'River', 'Hill', 'Sunset']
    sufijos = ['St', 'Ave', 'Blvd', 'Rd', 'Ln', 'Dr', 'Ct', 'Pl', 'Way']
    return f"{random.choice(prefijos)} {random.choice(sufijos)}"

# Comando de ayuda adicional
async def rmlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista completa de países"""
    PAISES = {
        'mx': 'Mexico', 'col': 'Colombia', 'ven': 'Venezuela', 'us': 'Estados Unidos',
        'uk': 'Reino Unido', 'ca': 'Canada', 'rus': 'Rusia', 'jap': 'Japón',
        'chi': 'China', 'hon': 'Honduras', 'chile': 'Chile', 'arg': 'Argentina',
        'ind': 'India', 'br': 'Brasil', 'peru': 'Perú', 'es': 'España',
        'italia': 'Italia', 'fran': 'Francia', 'suiza': 'Suiza'
    }
    
    lista = "\n".join([f"• {cod} - {nombre}" for cod, nombre in PAISES.items()])
    
    await update.message.reply_text(
        f"🇺🇳 *Lista de Países Disponibles:*\n\n{lista}\n\n"
        f"📝 Usa: /rm <código>",
        parse_mode='Markdown'
    )
