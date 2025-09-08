from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext

# Diccionario completo de países
PAISES_COMPLETO = {
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

async def rmlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para mostrar la lista de países con botones de paginación"""
    await show_rmlist_page(update, context, page=0)

async def show_rmlist_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Muestra una página específica de la lista de países"""
    
    # Dividir la lista en páginas de 10 países cada una
    paises_list = list(PAISES_COMPLETO.items())
    items_per_page = 10
    total_pages = (len(paises_list) + items_per_page - 1) // items_per_page
    
    # Asegurar que la página esté dentro del rango válido
    page = max(0, min(page, total_pages - 1))
    
    # Calcular el rango de países para esta página
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(paises_list))
    
    # Crear el mensaje HTML
    html_message = f"<b>🌍 LISTA DE PAÍSES DISPONIBLES</b>\n\n"
    html_message += f"<b>📋 Página {page + 1} de {total_pages}</b>\n\n"
    
    # Agregar países de la página actual
    for i in range(start_idx, end_idx):
        codigo, info = paises_list[i]
        html_message += f"{info['bandera']} <code>{codigo}</code> - {info['nombre']}\n"
    
    html_message += f"\n<b>💡 Mostrando {end_idx - start_idx} de {len(paises_list)} países</b>\n\n"
    html_message += "<b>📍 USO:</b> <code>/rm codigo_pais</code>\n"
    html_message += "<b>📍 EJEMPLO:</b> <code>/rm mx</code> para México\n"
    html_message += "<b>📍 EJEMPLO:</b> <code>/rm us</code> para USA\n"
    
    # Crear botones de paginación
    keyboard = []
    
    if total_pages > 1:
        row = []
        if page > 0:
            row.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"rmlist_prev_{page}"))
        
        # Botón de página actual (solo para mostrar)
        row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="rmlist_current"))
        
        if page < total_pages - 1:
            row.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"rmlist_next_{page}"))
        
        keyboard.append(row)
    
    # Botón para cerrar
    keyboard.append([InlineKeyboardButton("❌ Cerrar Lista", callback_data="rmlist_close")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Enviar o editar el mensaje
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                html_message, 
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        except Exception as e:
            # Si hay error al editar, enviar nuevo mensaje
            await update.callback_query.message.reply_text(
                html_message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            html_message, 
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def rmlist_callback(update: Update, context: CallbackContext):
    """Maneja los callbacks de los botones de paginación"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "rmlist_close":
        await query.delete_message()
    elif data == "rmlist_current":
        # No hacer nada para el botón de página actual
        pass
    elif data.startswith("rmlist_prev_"):
        current_page = int(data.split("_")[2])
        await show_rmlist_page(update, context, page=current_page - 1)
    elif data.startswith("rmlist_next_"):
        current_page = int(data.split("_")[2])
        await show_rmlist_page(update, context, page=current_page + 1)