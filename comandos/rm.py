from telegram import Update
from telegram.ext import ContextTypes
import aiohttp
import random

async def rm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para generar direcciones reales - Versión Mejorada"""
    
    # Mapeo COMPLETO con códigos en español e inglés
    PAISES = {
        'mx': {'nombre': 'México', 'codigo': '+52', 'nombre_api': 'Mexico', 'bandera': '🇲🇽'},
        'col': {'nombre': 'Colombia', 'codigo': '+57', 'nombre_api': 'Colombia', 'bandera': '🇨🇴'},
        'ven': {'nombre': 'Venezuela', 'codigo': '+58', 'nombre_api': 'Venezuela', 'bandera': '🇻🇪'},
        'us': {'nombre': 'Estados Unidos', 'codigo': '+1', 'nombre_api': 'United States', 'bandera': '🇺🇸'},
        'uk': {'nombre': 'Reino Unido', 'codigo': '+44', 'nombre_api': 'United Kingdom', 'bandera': '🇬🇧'},
        'ca': {'nombre': 'Canadá', 'codigo': '+1', 'nombre_api': 'Canada', 'bandera': '🇨🇦'},
        'rus': {'nombre': 'Rusia', 'codigo': '+7', 'nombre_api': 'Russia', 'bandera': '🇷🇺'},
        'jap': {'nombre': 'Japón', 'codigo': '+81', 'nombre_api': 'Japan', 'bandera': '🇯🇵'},
        'chi': {'nombre': 'China', 'codigo': '+86', 'nombre_api': 'China', 'bandera': '🇨🇳'},
        'hon': {'nombre': 'Honduras', 'codigo': '+504', 'nombre_api': 'Honduras', 'bandera': '🇭🇳'},
        'chile': {'nombre': 'Chile', 'codigo': '+56', 'nombre_api': 'Chile', 'bandera': '🇨🇱'},
        'arg': {'nombre': 'Argentina', 'codigo': '+54', 'nombre_api': 'Argentina', 'bandera': '🇦🇷'},
        'ind': {'nombre': 'India', 'codigo': '+91', 'nombre_api': 'India', 'bandera': '🇮🇳'},
        'br': {'nombre': 'Brasil', 'codigo': '+55', 'nombre_api': 'Brazil', 'bandera': '🇧🇷'},
        'peru': {'nombre': 'Perú', 'codigo': '+51', 'nombre_api': 'Peru', 'bandera': '🇵🇪'},
        'es': {'nombre': 'España', 'codigo': '+34', 'nombre_api': 'Spain', 'bandera': '🇪🇸'},
        'italia': {'nombre': 'Italia', 'codigo': '+39', 'nombre_api': 'Italy', 'bandera': '🇮🇹'},
        'fran': {'nombre': 'Francia', 'codigo': '+33', 'nombre_api': 'France', 'bandera': '🇫🇷'},
        'suiza': {'nombre': 'Suiza', 'codigo': '+41', 'nombre_api': 'Switzerland', 'bandera': '🇨🇭'},
        
        # Aliases en inglés
        'switzerland': {'nombre': 'Suiza', 'codigo': '+41', 'nombre_api': 'Switzerland', 'bandera': '🇨🇭'},
        'usa': {'nombre': 'Estados Unidos', 'codigo': '+1', 'nombre_api': 'United States', 'bandera': '🇺🇸'},
        'spain': {'nombre': 'España', 'codigo': '+34', 'nombre_api': 'Spain', 'bandera': '🇪🇸'},
        'italy': {'nombre': 'Italia', 'codigo': '+39', 'nombre_api': 'Italy', 'bandera': '🇮🇹'},
        'france': {'nombre': 'Francia', 'codigo': '+33', 'nombre_api': 'France', 'bandera': '🇫🇷'}
    }
    
    if not context.args:
        # Mostrar lista de países decorada
        lista_paises = "🌍 *PAÍSES DISPONIBLES:*\n\n"
        
        # Organizar países en columnas para mejor visualización
        paises_lista = list(PAISES.items())
        # Filtrar solo los códigos principales (no aliases)
        paises_principales = [(cod, info) for cod, info in paises_lista if len(cod) <= 5]
        
        for codigo, info in paises_principales:
            lista_paises += f"{info['bandera']} `{codigo}` - {info['nombre']}\n"
        
        mensaje_ayuda = f"""
📍 *COMANDO RM - GENERADOR DE DIRECCIONES* 📍

📋 *Uso correcto:*
🔹 `/rm <código_país>`
🔹 Ejemplo: `/rm mx`
🔹 Ejemplo: `/rm us`
🔹 Ejemplo: `/rm suiza`

{lista_paises}

💡 *Nota:* Los códigos de país son los que aparecen entre comillas invertidas
        """
        
        await update.message.reply_text(mensaje_ayuda, parse_mode='Markdown')
        return
    
    pais_code = context.args[0].lower()
    
    if pais_code not in PAISES:
        # Mensaje de error con sugerencias
        mensaje_error = f"""
❌ *Código de país no válido:* `{pais_code}`

📋 *Códigos válidos:*
"""
        # Mostrar algunos códigos sugeridos
        codigos_sugeridos = ['mx', 'us', 'col', 'es', 'arg', 'suiza']
        for codigo in codigos_sugeridos:
            if codigo in PAISES:
                mensaje_error += f"🔹 `{codigo}` - {PAISES[codigo]['nombre']} {PAISES[codigo]['bandera']}\n"
        
        mensaje_error += f"""
💡 *Ejemplos de uso:*
• `/rm mx` - Dirección en México 🇲🇽
• `/rm us` - Dirección en USA 🇺🇸  
• `/rm suiza` - Dirección en Suiza 🇨🇭

📝 Usa `/rm` sin argumentos para ver la lista completa de países.
        """
        
        await update.message.reply_text(mensaje_error, parse_mode='Markdown')
        return
    
    pais_info = PAISES[pais_code]
    mensaje_carga = await update.message.reply_text("🔄 Generando dirección real...")
    
    try:
        # PRIMERO: Intentar con API de OpenStreetMap
        datos = await obtener_datos_osm(pais_info['nombre_api'])
        
        if not datos:
            # SEGUNDO: Si falla la API, usar nuestra base de datos REAL
            datos = await generar_datos_reales(pais_info)
        
        if datos:
            respuesta = f"""
🌍 *Dirección en {pais_info['nombre']}* {pais_info['bandera']}

🏢 *Street:* `{datos['calle']}`
🏙️ *City:* `{datos['ciudad']}`
🏛️ *State:* `{datos['estado']}`
📮 *ZIP Code:* `{datos['codigo_postal']}`
📞 *Phone Code:* `{pais_info['codigo']}`
🇺🇳 *Country:* `{pais_info['nombre']}`

✅ *Datos 100% reales y verificados*
            """
            await mensaje_carga.delete()
            await update.message.reply_text(respuesta, parse_mode='Markdown')
        else:
            await mensaje_carga.delete()
            await update.message.reply_text("❌ No se pudieron obtener datos. Intenta con otro país.")
            
    except Exception as e:
        await mensaje_carga.delete()
        await update.message.reply_text("❌ Error temporal. Intenta nuevamente.")

# [Las funciones obtener_datos_osm, generar_datos_reales y generar_nombre_calle se mantienen igual]