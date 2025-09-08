from telegram import Update
from telegram.ext import ContextTypes

async def rmlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para mostrar la lista de países en formato HTML"""
    
    PAISES = {
        'mx': {'nombre': 'México', 'codigo': '+52', 'bandera': '🇲🇽'},
        'col': {'nombre': 'Colombia', 'codigo': '+57', 'bandera': '🇨🇴'},
        'ven': {'nombre': 'Venezuela', 'codigo': '+58', 'bandera': '🇻🇪'},
        'us': {'nombre': 'Estados Unidos', 'codigo': '+1', 'bandera': '🇺🇸'},
        'uk': {'nombre': 'Reino Unido', 'codigo': '+44', 'bandera': '🇬🇧'},
        'ca': {'nombre': 'Canadá', 'codigo': '+1', 'bandera': '🇨🇦'},
        'rus': {'nombre': 'Rusia', 'codigo': '+7', 'bandera': '🇷🇺'},
        'jap': {'nombre': 'Japón', 'codigo': '+81', 'bandera': '🇯🇵'},
        'chi': {'nombre': 'China', 'codigo': '+86', 'bandera': '🇨🇳'},
        'hon': {'nombre': 'Honduras', 'codigo': '+504', 'bandera': '🇭🇳'},
        'chile': {'nombre': 'Chile', 'codigo': '+56', 'bandera': '🇨🇱'},
        'arg': {'nombre': 'Argentina', 'codigo': '+54', 'bandera': '🇦🇷'},
        'ind': {'nombre': 'India', 'codigo': '+91', 'bandera': '🇮🇳'},
        'br': {'nombre': 'Brasil', 'codigo': '+55', 'bandera': '🇧🇷'},
        'peru': {'nombre': 'Perú', 'codigo': '+51', 'bandera': '🇵🇪'},
        'es': {'nombre': 'España', 'codigo': '+34', 'bandera': '🇪🇸'},
        'italia': {'nombre': 'Italia', 'codigo': '+39', 'bandera': '🇮🇹'},
        'fran': {'nombre': 'Francia', 'codigo': '+33', 'bandera': '🇫🇷'},
        'suiza': {'nombre': 'Suiza', 'codigo': '+41', 'bandera': '🇨🇭'},
    }
    
    # Crear lista en formato HTML
    html_lista = "<b>🌍 LISTA DE PAÍSES DISPONIBLES</b>\n\n"
    html_lista += "<b>📋 CÓDIGOS VÁLIDOS:</b>\n\n"
    
    # Organizar en columnas para mejor visualización
    paises_items = list(PAISES.items())
    mitad = len(paises_items) // 2 + len(paises_items) % 2
    
    for i in range(mitad):
        linea = ""
        # Primera columna
        if i < len(paises_items):
            codigo1, info1 = paises_items[i]
            linea += f"<b>{info1['bandera']} {codigo1}</b> - {info1['nombre']}"
        
        # Segunda columna (si existe)
        if i + mitad < len(paises_items):
            codigo2, info2 = paises_items[i + mitad]
            # Añadir espacios para alinear
            espacios = " " * (12 - len(codigo1) - len(info1['nombre']))
            linea += f"{espacios}<b>{info2['bandera']} {codigo2}</b> - {info2['nombre']}"
        
        html_lista += linea + "\n"
    
    html_lista += "\n<b>💡 EJEMPLOS DE USO:</b>\n"
    html_lista += "• <code>/rm mx</code> - Dirección en México 🇲🇽\n"
    html_lista += "• <code>/rm us</code> - Dirección en USA 🇺🇸\n"
    html_lista += "• <code>/rm suiza</code> - Dirección en Suiza 🇨🇭\n"
    html_lista += "• <code>/rm es</code> - Dirección en España 🇪🇸\n\n"
    html_lista += "<b>📍 NOTA:</b> Usa los códigos entre comillas simples"
    
    await update.message.reply_text(html_lista, parse_mode='HTML')