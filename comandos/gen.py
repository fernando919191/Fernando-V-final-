from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
import random
import re
import logging
from datetime import datetime

# Estados del flujo (para modo conversación)
STATE_BIN, STATE_QTY, STATE_EXP, STATE_CVV = range(4)

# Esquemas de marcas
CARD_SCHEMES = {
    "visa":       {"lengths": [16], "prefixes": ["4"], "cvv_len": 3},
    "mastercard": {"lengths": [16], "prefixes": ["51","52","53","54","55"], "cvv_len": 3},
    "amex":       {"lengths": [15], "prefixes": ["34","37"], "cvv_len": 4},
    "diners":     {"lengths": [14], "prefixes": ["300","301","302","303","304","305","36","38"], "cvv_len": 3},
    "discover":   {"lengths": [16], "prefixes": ["6011","65"], "cvv_len": 3},
    "jcb":        {"lengths": [16], "prefixes": ["35"], "cvv_len": 3},
}

# =========================
# Utilidades
# =========================
def detect_brand(bin_prefix: str):
    for brand, data in CARD_SCHEMES.items():
        if any(bin_prefix.startswith(pref) for pref in data["prefixes"]):
            return brand, data["lengths"][0], data["cvv_len"]
    return None, None, None

def luhn_checksum(number: int) -> int:
    digits = [int(d) for d in str(number)]
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d = d * 2
            if d > 9:
                d -= 9
        total += d
    return total % 10

def calculate_luhn(partial: int) -> int:
    return (10 - luhn_checksum(partial * 10)) % 10

def parse_exp_input(txt: str):
    t = txt.strip().lower()
    if t in ["skip", "aleatorio", "random", "s", ""]:
        return None

    # Aceptar MM/YY, MM-YY, MMYY, MM YY
    m = re.match(r"^(0[1-9]|1[0-2])[/\-\s]?(\d{2,4})$", t)
    if not m:
        return "ERROR"

    month = m.group(1)
    year_part = m.group(2)
    
    if len(year_part) == 2:
        year4 = f"20{year_part}"
    else:
        year4 = year_part
        
    return (month, year4)

def generate_cards(bin_prefix: str, qty: int, exp_tuple, cvv_input: str | None):
    brand, length, cvv_len = detect_brand(bin_prefix)
    if not brand:
        return [], 3
        
    rem = length - len(bin_prefix) - 1
    cards = []
    for _ in range(qty):
        middle = ''.join(str(random.randint(0, 9)) for _ in range(rem))
        partial = int(bin_prefix + middle)
        number = bin_prefix + middle + str(calculate_luhn(partial))

        if exp_tuple is None:
            month = f"{random.randint(1,12):02d}"
            year4 = str(random.randint(datetime.now().year + 1, datetime.now().year + 5))
        else:
            month, year4 = exp_tuple

        if cvv_input:
            cvv = cvv_input
        else:
            cvv = ''.join(str(random.randint(0, 9)) for _ in range(cvv_len))

        cards.append(f"{number}|{month}|{year4}|{cvv}")

    return cards, cvv_len

def parse_direct_command(text: str):
    """Parsea comandos directos - formato flexible"""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None, None, None, 10
        
    param_str = parts[1].strip()
    
    # Detectar qué separadores se están usando
    if '|' in param_str:
        separator = '|'
    elif '/' in param_str:
        separator = '/'
    else:
        # Si no hay separadores, es solo el BIN
        return param_str, None, None, 10
    
    params = param_str.split(separator)
    bin_input = params[0].strip()
    
    # Limpiar parámetros vacíos
    params = [p.strip() for p in params if p.strip()]
    
    if len(params) < 1:
        return None, None, None, 10
        
    bin_input = params[0]
    exp_input = params[1] if len(params) > 1 else None
    cvv_input = params[2] if len(params) > 2 else None
    
    # Cantidad - por defecto 10
    if len(params) > 3 and params[3].isdigit():
        qty_input = int(params[3])
    else:
        qty_input = 10
        
    qty_input = max(1, min(qty_input, 20))
    
    return bin_input, exp_input, cvv_input, qty_input

# =========================
# Handlers Principales
# =========================
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja /gen con parámetros directos"""
    try:
        if context.args:
            # Modo directo
            bin_input, exp_input, cvv_input, qty = parse_direct_command(update.message.text)
            
            if not bin_input or not bin_input.isdigit():
                await update.message.reply_text(
                    "❌ Formato incorrecto. Ejemplos:\n"
                    "• `/gen 416916` - 10 tarjetas\n"
                    "• `/gen 416916|12|25` - Con fecha\n" 
                    "• `/gen 416916/12/25/123` - Con CVV\n"
                    "• `/gen 416916|12|25|123|5` - 5 tarjetas\n\n"
                    "💡 Usa `|` o `/` como separadores",
                    parse_mode='Markdown'
                )
                return
                
            brand, length, cvv_len = detect_brand(bin_input)
            if not brand:
                await update.message.reply_text("❌ BIN no válido o no soportado.")
                return
            
            # Procesar expiración
            exp_tuple = None
            if exp_input:
                parsed = parse_exp_input(exp_input)
                if parsed == "ERROR":
                    await update.message.reply_text("❌ Fecha inválida. Usa: MM/YY, MM-YY, MMYY")
                    return
                exp_tuple = parsed
            
            # Validar CVV
            if cvv_input and (not cvv_input.isdigit() or len(cvv_input) != cvv_len):
                await update.message.reply_text(f"❌ CVV debe tener {cvv_len} dígitos.")
                return
            
            # Generar tarjetas
            cards, _ = generate_cards(bin_input, qty, exp_tuple, cvv_input)
            
            if not cards:
                await update.message.reply_text("❌ Error generando tarjetas.")
                return
            
            response = f"💳 *{len(cards)} tarjeta(s) generada(s):*\n```\n" + "\n".join(cards) + "\n```"
            await update.message.reply_text(response, parse_mode='Markdown')
            
        else:
            # Modo conversación
            await update.message.reply_text(
                "💳 *GENERADOR DE TARJETAS*\n\n"
                "Envía un BIN (6-8 dígitos) para comenzar.\n"
                "O usa modo directo:\n"
                "• `/gen 416916` - 10 tarjetas\n"
                "• `/gen 416916/12/25` - Con fecha\n"
                "• `/gen 416916|12|25|123` - Con CVV\n\n"
                "💡 Puedes usar `|` o `/` como separadores\n"
                "Escribe /cancel para salir.",
                parse_mode='Markdown'
            )
            context.user_data['in_conversation'] = True
            return STATE_BIN
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END

# =========================
# Handlers de Conversación 
# =========================
async def bin_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    binp = update.message.text.strip()
    if not binp.isdigit():
        return await update.message.reply_text("❌ El BIN debe contener solo dígitos.")
    
    brand, length, cvv_len = detect_brand(binp)
    if not brand:
        return await update.message.reply_text("❌ BIN desconocido. Prueba con un BIN válido.")
    
    context.user_data['bin'] = binp
    context.user_data['cvv_len'] = cvv_len
    
    await update.message.reply_text(
        f"✅ *Marca detectada:* {brand.upper()}\n"
        f"• Dígitos: {length}\n"
        f"• CVV: {cvv_len} dígitos\n\n"
        "¿Cuántas tarjetas deseas generar? (1-20)\n"
        "💡 Por defecto: 10 tarjetas",
        parse_mode='Markdown'
    )
    return STATE_QTY

async def qty_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        if text == "":
            qty = 10
        else:
            qty = int(text)
            if qty <= 0 or qty > 20:
                return await update.message.reply_text("❌ La cantidad debe ser entre 1 y 20.")
    except ValueError:
        return await update.message.reply_text("❌ Debe ser un número entero.")
    
    context.user_data['qty'] = qty
    await update.message.reply_text(
        "📅 Ingresa fecha de expiración:\n"
        "• Formato: MM/YY, MM-YY, MMYY\n"
        "• 'skip' para aleatoria\n"
        "• Enter para aleatoria\n"
        "• /cancel para salir"
    )
    return STATE_EXP

async def exp_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    if txt == "":
        parsed = None
    else:
        parsed = parse_exp_input(txt)
        if parsed == "ERROR":
            return await update.message.reply_text("❌ Formato inválido. Usa: MM/YY, MM-YY, MMYY")
    
    context.user_data['exp'] = parsed
    cvv_len = context.user_data.get('cvv_len', 3)
    
    await update.message.reply_text(
        f"🔒 Ingresa CVV ({cvv_len} dígitos):\n"
        "• 'skip' para aleatorio\n"
        "• Enter para aleatorio\n"
        "• /cancel para salir"
    )
    return STATE_CVV

async def cvv_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    cvv_len = context.user_data.get('cvv_len', 3)
    
    if txt in ["skip", "aleatorio", "random", "s", ""]:
        cvv_value = None
    else:
        if not re.fullmatch(r"\d{"+str(cvv_len)+r"}", txt):
            return await update.message.reply_text(f"❌ El CVV debe tener {cvv_len} dígitos.")
        cvv_value = txt

    context.user_data['cvv'] = cvv_value
    data = context.user_data
    
    qty = data.get('qty', 10)
    cards, _ = generate_cards(data['bin'], qty, data['exp'], data['cvv'])
    
    response = f"💳 *{len(cards)} tarjeta(s) generada(s):*\n```\n" + "\n".join(cards) + "\n```"
    await update.message.reply_text(response, parse_mode='Markdown')
    
    context.user_data.pop('in_conversation', None)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada.")
    context.user_data.pop('in_conversation', None)
    return ConversationHandler.END

# =========================
# Registro del comando
# =========================
def setup(app):
    """Registra el comando de conversación"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("gen", gen)],
        states={
            STATE_BIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bin_received)],
            STATE_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, qty_received)],
            STATE_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, exp_received)],
            STATE_CVV: [MessageHandler(filters.TEXT & ~filters.COMMAND, cvv_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    return conv_handler