from telegram import Update
from telegram.ext import ContextTypes
import aiohttp
import random
import asyncio

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para generar direcciones reales - Versión Mejorada"""
    
    # Mapeo COMPLETO con más países y códigos
    PAISES = {
        # América
        'mx': {'nombre': 'Mexico', 'codigo': '+52', 'nombre_api': 'Mexico'},
        'col': {'nombre': 'Colombia', 'codigo': '+57', 'nombre_api': 'Colombia'},
        'ven': {'nombre': 'Venezuela', 'codigo': '+58', 'nombre_api': 'Venezuela'},
        'us': {'nombre': 'Estados Unidos', 'codigo': '+1', 'nombre_api': 'United States'},
        'usa': {'nombre': 'Estados Unidos', 'codigo': '+1', 'nombre_api': 'United States'},
        'ca': {'nombre': 'Canada', 'codigo': '+1', 'nombre_api': 'Canada'},
        'br': {'nombre': 'Brasil', 'codigo': '+55', 'nombre_api': 'Brazil'},
        'arg': {'nombre': 'Argentina', 'codigo': '+54', 'nombre_api': 'Argentina'},
        'chile': {'nombre': 'Chile', 'codigo': '+56', 'nombre_api': 'Chile'},
        'peru': {'nombre': 'Perú', 'codigo': '+51', 'nombre_api': 'Peru'},
        'ecu': {'nombre': 'Ecuador', 'codigo': '+593', 'nombre_api': 'Ecuador'},
        'uru': {'nombre': 'Uruguay', 'codigo': '+598', 'nombre_api': 'Uruguay'},
        'par': {'nombre': 'Paraguay', 'codigo': '+595', 'nombre_api': 'Paraguay'},
        'bol': {'nombre': 'Bolivia', 'codigo': '+591', 'nombre_api': 'Bolivia'},
        'cri': {'nombre': 'Costa Rica', 'codigo': '+506', 'nombre_api': 'Costa Rica'},
        'pan': {'nombre': 'Panamá', 'codigo': '+507', 'nombre_api': 'Panama'},
        'rep': {'nombre': 'República Dominicana', 'codigo': '+1-809', 'nombre_api': 'Dominican Republic'},
        'hon': {'nombre': 'Honduras', 'codigo': '+504', 'nombre_api': 'Honduras'},
        'sal': {'nombre': 'El Salvador', 'codigo': '+503', 'nombre_api': 'El Salvador'},
        'gua': {'nombre': 'Guatemala', 'codigo': '+502', 'nombre_api': 'Guatemala'},
        'nic': {'nombre': 'Nicaragua', 'codigo': '+505', 'nombre_api': 'Nicaragua'},
        
        # Europa
        'uk': {'nombre': 'Reino Unido', 'codigo': '+44', 'nombre_api': 'United Kingdom'},
        'es': {'nombre': 'España', 'codigo': '+34', 'nombre_api': 'Spain'},
        'spain': {'nombre': 'España', 'codigo': '+34', 'nombre_api': 'Spain'},
        'fr': {'nombre': 'Francia', 'codigo': '+33', 'nombre_api': 'France'},
        'fran': {'nombre': 'Francia', 'codigo': '+33', 'nombre_api': 'France'},
        'france': {'nombre': 'Francia', 'codigo': '+33', 'nombre_api': 'France'},
        'de': {'nombre': 'Alemania', 'codigo': '+49', 'nombre_api': 'Germany'},
        'ger': {'nombre': 'Alemania', 'codigo': '+49', 'nombre_api': 'Germany'},
        'it': {'nombre': 'Italia', 'codigo': '+39', 'nombre_api': 'Italy'},
        'italia': {'nombre': 'Italia', 'codigo': '+39', 'nombre_api': 'Italy'},
        'italy': {'nombre': 'Italia', 'codigo': '+39', 'nombre_api': 'Italy'},
        'pt': {'nombre': 'Portugal', 'codigo': '+351', 'nombre_api': 'Portugal'},
        'por': {'nombre': 'Portugal', 'codigo': '+351', 'nombre_api': 'Portugal'},
        'nl': {'nombre': 'Países Bajos', 'codigo': '+31', 'nombre_api': 'Netherlands'},
        'bel': {'nombre': 'Bélgica', 'codigo': '+32', 'nombre_api': 'Belgium'},
        'swiss': {'nombre': 'Suiza', 'codigo': '+41', 'nombre_api': 'Switzerland'},
        'suiza': {'nombre': 'Suiza', 'codigo': '+41', 'nombre_api': 'Switzerland'},
        'switzerland': {'nombre': 'Suiza', 'codigo': '+41', 'nombre_api': 'Switzerland'},
        'sue': {'nombre': 'Suecia', 'codigo': '+46', 'nombre_api': 'Sweden'},
        'nor': {'nombre': 'Noruega', 'codigo': '+47', 'nombre_api': 'Norway'},
        'din': {'nombre': 'Dinamarca', 'codigo': '+45', 'nombre_api': 'Denmark'},
        'fin': {'nombre': 'Finlandia', 'codigo': '+358', 'nombre_api': 'Finland'},
        'aus': {'nombre': 'Austria', 'codigo': '+43', 'nombre_api': 'Austria'},
        'gre': {'nombre': 'Grecia', 'codigo': '+30', 'nombre_api': 'Greece'},
        'pol': {'nombre': 'Polonia', 'codigo': '+48', 'nombre_api': 'Poland'},
        'rus': {'nombre': 'Rusia', 'codigo': '+7', 'nombre_api': 'Russia'},
        'tur': {'nombre': 'Turquía', 'codigo': '+90', 'nombre_api': 'Turkey'},
        'ucr': {'nombre': 'Ucrania', 'codigo': '+380', 'nombre_api': 'Ukraine'},
        
        # Asia
        'chi': {'nombre': 'China', 'codigo': '+86', 'nombre_api': 'China'},
        'china': {'nombre': 'China', 'codigo': '+86', 'nombre_api': 'China'},
        'jap': {'nombre': 'Japón', 'codigo': '+81', 'nombre_api': 'Japan'},
        'japan': {'nombre': 'Japón', 'codigo': '+81', 'nombre_api': 'Japan'},
        'ind': {'nombre': 'India', 'codigo': '+91', 'nombre_api': 'India'},
        'india': {'nombre': 'India', 'codigo': '+91', 'nombre_api': 'India'},
        'kor': {'nombre': 'Corea del Sur', 'codigo': '+82', 'nombre_api': 'South Korea'},
        'tai': {'nombre': 'Taiwán', 'codigo': '+886', 'nombre_api': 'Taiwan'},
        'sin': {'nombre': 'Singapur', 'codigo': '+65', 'nombre_api': 'Singapore'},
        'mal': {'nombre': 'Malasia', 'codigo': '+60', 'nombre_api': 'Malaysia'},
        'tai': {'nombre': 'Tailandia', 'codigo': '+66', 'nombre_api': 'Thailand'},
        'vie': {'nombre': 'Vietnam', 'codigo': '+84', 'nombre_api': 'Vietnam'},
        'fil': {'nombre': 'Filipinas', 'codigo': '+63', 'nombre_api': 'Philippines'},
        'indo': {'nombre': 'Indonesia', 'codigo': '+62', 'nombre_api': 'Indonesia'},
        'isr': {'nombre': 'Israel', 'codigo': '+972', 'nombre_api': 'Israel'},
        'eme': {'nombre': 'Emiratos Árabes', 'codigo': '+971', 'nombre_api': 'United Arab Emirates'},
        'arab': {'nombre': 'Arabia Saudita', 'codigo': '+966', 'nombre_api': 'Saudi Arabia'},
        
        # Oceanía
        'aus': {'nombre': 'Australia', 'codigo': '+61', 'nombre_api': 'Australia'},
        'nz': {'nombre': 'Nueva Zelanda', 'codigo': '+64', 'nombre_api': 'New Zealand'},
        
        # África
        'eg': {'nombre': 'Egipto', 'codigo': '+20', 'nombre_api': 'Egypt'},
        'mor': {'nombre': 'Marruecos', 'codigo': '+212', 'nombre_api': 'Morocco'},
        'sa': {'nombre': 'Sudáfrica', 'codigo': '+27', 'nombre_api': 'South Africa'},
        'nig': {'nombre': 'Nigeria', 'codigo': '+234', 'nombre_api': 'Nigeria'},
        'ken': {'nombre': 'Kenia', 'codigo': '+254', 'nombre_api': 'Kenya'},
    }
    
    if not context.args:
        lista_paises = "\n".join([f"• {codigo} - {info['nombre']}" for codigo, info in list(PAISES.items())[:20]])
        await update.message.reply_text(
            f"🌍 *Comando RM - Generador de Direcciones*\n\n"
            f"📝 Uso: /rm <código_país>\n\n"
            f"🇺🇳 *Países disponibles (primeros 20):*\n{lista_paises}\n\n"
            f"📋 Usa /rmlist para ver todos los países\n"
            f"Ejemplo: /rm mx para datos de México\n"
            f"Ejemplo: /rm suiza para datos de Suiza",
            parse_mode='Markdown'
        )
        return
    
    pais_code = context.args[0].lower()
    
    if pais_code not in PAISES:
        # Mostrar sugerencias similares
        sugerencias = [cod for cod in PAISES.keys() if pais_code in cod or cod in pais_code][:5]
        mensaje_error = "❌ Código de país no válido.\n\n💡 Países similares:\n"
        if sugerencias:
            mensaje_error += "\n".join([f"• {cod} - {PAISES[cod]['nombre']}" for cod in sugerencias])
        else:
            mensaje_error += "• mx - Mexico\n• col - Colombia\n• us - USA\n• es - España\n• arg - Argentina"
            
        mensaje_error += "\n\n📋 Usa /rmlist para ver todos los países"
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
        'Colombia': {
            'ciudades': [
                {'nombre': 'Bogotá', 'estado': 'Cundinamarca', 'cp': '11001', 'calles': ['Carrera 7', 'Calle 100', 'Avenida Boyacá', 'Autopista Norte']},
                {'nombre': 'Medellín', 'estado': 'Antioquia', 'cp': '05001', 'calles': ['Avenida Poblado', 'Carrera 70', 'Avenida Oriental', 'Circular']},
                {'nombre': 'Cali', 'estado': 'Valle del Cauca', 'cp': '76001', 'calles': ['Avenida Sexta', 'Carrera 1', 'Avenida Pasoancho', 'Circunvalar']},
                {'nombre': 'Barranquilla', 'estado': 'Atlántico', 'cp': '08001', 'calles': ['Carrera 51', 'Calle 84', 'Vía 40', 'Circunvalar']}
            ]
        },
        'Spain': {
            'ciudades': [
                {'nombre': 'Madrid', 'estado': 'Madrid', 'cp': '28001', 'calles': ['Gran Vía', 'Paseo de la Castellana', 'Calle de Alcalá', 'Calle Mayor']},
                {'nombre': 'Barcelona', 'estado': 'Cataluña', 'cp': '08001', 'calles': ['Las Ramblas', 'Paseo de Gracia', 'Diagonal', 'Calle de Balmes']},
                {'nombre': 'Valencia', 'estado': 'Valencia', 'cp': '46001', 'calles': ['Calle de la Paz', 'Gran Vía Marqués del Turia', 'Calle de Colón', 'Avenida del Puerto']},
                {'nombre': 'Sevilla', 'estado': 'Andalucía', 'cp': '41001', 'calles': ['Avenida de la Constitución', 'Calle Sierpes', 'Avenida de Kansas City', 'Calle Betis']}
            ]
        },
        'Argentina': {
            'ciudades': [
                {'nombre': 'Buenos Aires', 'estado': 'CABA', 'cp': 'C1001', 'calles': ['Avenida 9 de Julio', 'Avenida Corrientes', 'Florida', 'Avenida Rivadavia']},
                {'nombre': 'Córdoba', 'estado': 'Córdoba', 'cp': '5000', 'calles': ['Avenida Colón', 'Avenida Vélez Sarsfield', 'Cañada', 'Avenida General Paz']},
                {'nombre': 'Rosario', 'estado': 'Santa Fe', 'cp': 'S2000', 'calles': ['Calle Córdoba', 'Boulevard Oroño', 'Avenida Pellegrini', 'Avenida Circunvalación']},
                {'nombre': 'Mendoza', 'estado': 'Mendoza', 'cp': '5500', 'calles': ['Avenida San Martín', 'Avenida Las Heras', 'Avenida Boulogne Sur Mer', 'Avenida España']}
            ]
        },
        'Brazil': {
            'ciudades': [
                {'nombre': 'São Paulo', 'estado': 'SP', 'cp': '01000', 'calles': ['Avenida Paulista', 'Rua Augusta', 'Avenida Faria Lima', 'Rua Oscar Freire']},
                {'nombre': 'Rio de Janeiro', 'estado': 'RJ', 'cp': '20000', 'calles': ['Avenida Atlântica', 'Rua Visconde de Pirajá', 'Avenida Brasil', 'Rua do Ouvidor']},
                {'nombre': 'Brasília', 'estado': 'DF', 'cp': '70000', 'calles': ['Eixo Monumental', 'Asa Sul', 'Asa Norte', 'Avenida W3']},
                {'nombre': 'Salvador', 'estado': 'BA', 'cp': '40000', 'calles': ['Avenida Sete de Setembro', 'Avenida Oceanica', 'Rua Chile', 'Avenida Bonfim']}
            ]
        },
        'Chile': {
            'ciudades': [
                {'nombre': 'Santiago', 'estado': 'RM', 'cp': '8320000', 'calles': ['Alameda', 'Avenida Providencia', 'Avenida Las Condes', 'Avenida Vitacura']},
                {'nombre': 'Valparaíso', 'estado': 'Valparaíso', 'cp': '2340000', 'calles': ['Avenida Argentina', 'Avenida Errázuriz', 'Avenida Altamirano', 'Avenida Alemania']},
                {'nombre': 'Concepción', 'estado': 'Biobío', 'cp': '4030000', 'calles': ['Avenida Collao', 'Avenida Pedro de Valdivia', 'Avenida Arturo Prat', 'Avenida Chacabuco']}
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
        'usa': 'Estados Unidos', 'ca': 'Canada', 'br': 'Brasil', 'arg': 'Argentina',
        'chile': 'Chile', 'peru': 'Perú', 'ecu': 'Ecuador', 'uru': 'Uruguay',
        'par': 'Paraguay', 'bol': 'Bolivia', 'cri': 'Costa Rica', 'pan': 'Panamá',
        'rep': 'República Dominicana', 'hon': 'Honduras', 'sal': 'El Salvador',
        'gua': 'Guatemala', 'nic': 'Nicaragua', 'uk': 'Reino Unido', 'es': 'España',
        'spain': 'España', 'fr': 'Francia', 'de': 'Alemania', 'it': 'Italia',
        'pt': 'Portugal', 'nl': 'Países Bajos', 'bel': 'Bélgica', 'swiss': 'Suiza',
        'sue': 'Suecia', 'nor': 'Noruega', 'din': 'Dinamarca', 'fin': 'Finlandia',
        'aus': 'Austria', 'gre': 'Grecia', 'pol': 'Polonia', 'rus': 'Rusia',
        'tur': 'Turquía', 'ucr': 'Ucrania', 'chi': 'China', 'jap': 'Japón',
        'ind': 'India', 'kor': 'Corea del Sur', 'tai': 'Taiwán', 'sin': 'Singapur',
        'mal': 'Malasia', 'tai': 'Tailandia', 'vie': 'Vietnam', 'fil': 'Filipinas',
        'indo': 'Indonesia', 'isr': 'Israel', 'eme': 'Emiratos Árabes', 'arab': 'Arabia Saudita',
        'aus': 'Australia', 'nz': 'Nueva Zelanda', 'eg': 'Egipto', 'mor': 'Marruecos',
        'sa': 'Sudáfrica', 'nig': 'Nigeria', 'ken': 'Kenia'
    }
    
    # Dividir en columnas para mejor visualización
    paises_list = list(PAISES.items())
    mitad = len(paises_list) // 2
    columna1 = paises_list[:mitad]
    columna2 = paises_list[mitad:]
    
    lista_col1 = "\n".join([f"• {cod} - {nombre}" for cod, nombre in columna1])
    lista_col2 = "\n".join([f"• {cod} - {nombre}" for cod, nombre in columna2])
    
    await update.message.reply_text(
        f"🇺🇳 *Lista Completa de Países Disponibles:*\n\n"
        f"📋 *América:*\n{lista_col1}\n\n"
        f"📋 *Resto del Mundo:*\n{lista_col2}\n\n"
        f"🌍 Total: {len(PAISES)} países disponibles",
        parse_mode='Markdown'
    )
        f"📝 Usa: /rm <código>",
        parse_mode='Markdown'
    )
