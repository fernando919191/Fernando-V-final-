from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
import random
import re
import logging
from datetime import datetime

# Estados del flujo
STATE_BIN, STATE_QTY, STATE_EXP, STATE_CVV = range(4)

# Esquemas de marcas MEJORADO
CARD_SCHEMES = {
    "visa": {
        "lengths": [13, 16, 19], 
        "prefixes": ["4"], 
        "cvv_len": 3
    },
    "mastercard": {
        "lengths": [16], 
        "prefixes": ["51", "52", "53", "54", "55", "2221", "2222", "2223", "2224", "2225", "2226", "223", "224", "225", "226", "227", "228", "229", "23", "24", "25", "26", "27", "271", "2720"], 
        "cvv_len": 3
    },
    "amex": {
        "lengths": [15], 
        "prefixes": ["34", "37"], 
        "cvv_len": 4
    },
    "diners": {
        "lengths": [14, 16, 19], 
        "prefixes": ["300", "301", "302", "303", "304", "305", "36", "38"], 
        "cvv_len": 3
    },
    "discover": {
        "lengths": [16, 19], 
        "prefixes": ["6011", "65", "644", "645", "646", "647", "648", "649", "622126", "622925"], 
        "cvv_len": 3
    },
    "jcb": {
        "lengths": [16, 17, 18, 19], 
        "prefixes": ["35"], 
        "cvv_len": 3
    },
    "unionpay": {
        "lengths": [16, 17, 18, 19], 
        "prefixes": ["62"], 
        "cvv_len": 3
    },
    "maestro": {
        "lengths": [12, 13, 14, 15, 16, 17, 18, 19], 
        "prefixes": ["50", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69"], 
        "cvv_len": 3
    }
}

# =========================
# Utilidades MEJORADAS
# =========================
def detect_brand(bin_prefix: str):
    """Detecta la marca basado en los primeros dígitos"""
    # Usar primeros 6 dígitos para detección
    check_bin = bin_prefix[:6]
    
    for brand, data in CARD_SCHEMES.items():
        for prefix in data["prefixes"]:
            if check_bin.startswith(prefix):
                # Para la mayoría de tarjetas, usar la longitud más común
                if brand in ["visa", "mastercard", "discover", "jcb", "unionpay"]:
                    return brand, 16, data["cvv_len"]
                elif brand == "amex":
                    return brand, 15, data["cvv_len"]
                elif brand == "diners":
                    return brand, 16, data["cvv_len"]
                else:
                    return brand, data["lengths"][0], data["cvv_len"]
    
    # Si no se detecta marca, asumir Visa/Mastercard de 16 dígitos
    return "unknown", 16, 3

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

    # Aceptar MM/YY, MM-YY, MMYY
    m = re.match(r"^(0[1-9]|1[0-2])[/\-]?(\d{2})$", t)
    if not m:
        return "ERROR"

    month = m.group(1)
    year_part = m.group(2)
    year4 = f"20{year_part}"
        
    return (month, year4)

def generate_cards(bin_prefix: str, qty: int, exp_tuple, cvv_input: str | None):
    brand, length, cvv_len = detect_brand(bin_prefix)
    
    # Calcular dígitos restantes needed
    current_length = len(bin_prefix)
    rem = length - current_length - 1  # -1 para el dígito de Luhn
    
    # Si el BIN es muy largo, truncarlo
    if rem < 0:
        bin_prefix = bin_prefix[:length-1]
        current_length = len(bin_prefix)
        rem = length - current_length - 1
    
    cards = []
    
    for _ in range(qty):
        # Generar dígitos middle
        if rem > 0:
            middle = ''.join(str(random.randint(0, 9)) for _ in range(rem))
        else:
            middle = ''
            
        partial = int(bin_prefix + middle)
        number = bin_prefix + middle + str(calculate_luhn(partial))

        # Expiración
        if exp_tuple is None:
            month = f"{random.randint(1,12):02d}"
            year4 = str(random.randint(datetime.now().year + 1, datetime.now().year + 5))
        else:
            month, year4 = exp_tuple

        # CVV
        if cvv_input:
            cvv = cvv_input
        else:
            cvv = ''.join(str(random.randint(0, 9)) for _ in range(cvv_len))

        cards.append(f"{number}|{month}|{year4}|{cvv}")

    return cards, cvv_len

def parse_direct_command(text: str):
    """Parsea comandos directos"""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None, None, None, 10
        
    param_str = parts[1].strip()
    
    # Convertir cualquier separador a pipe |
    if '/' in param_str:
        param_str = param_str.replace('/', '|')
    if '-' in param_str:
        param_str = param_str.replace('-', '|')
    
    params = param_str.split('|')
    params = [p.strip() for p in params if p.strip()]
    
    if len(params) < 1:
        return None, None, None, 10
        
    bin_input = params[0]
    
    # Validar que el BIN sea numérico
    if not bin_input.isdigit():
        return None, None, None, 10
    
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
            bin_input, exp_input, cvv_input, qty = parse_direct_command(update.message.text)
            
            if not bin_input or not bin_input.isdigit() or len(bin_input) < 6:
                await update.message.reply_text(
                    "💳 *FORMATO:* `/gen BIN | MM | YY | CVV | CANTIDAD`\n\n"
                    "📋 *Ejemplos:*\n"
                    "• `/gen 416916` - 10 tarjetas\n"
                    "• `/gen 4169168384` - BIN de 8 dígitos\n"
                    "• `/gen 416916|12|25` - Con fecha\n" 
                    "• `/gen 416916|12|25|123|5` - 5 tarjetas\n\n"
                    "💡 BINs de 6-8+ dígitos aceptados",
                    parse_mode='Markdown'
                )
                return
                
            brand, length, cvv_len = detect_brand(bin_input)
            
            # Procesar expiración
            exp_tuple = None
            if exp_input:
                parsed = parse_exp_input(exp_input)
                if parsed == "ERROR":
                    await update.message.reply_text("❌ Fecha inválida. Usa: MM/YY o MM-YY")
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
                "Envía un BIN (6-8+ dígitos) para comenzar.\n"
                "O usa modo directo:\n"
                "• `/gen 416916` - 10 tarjetas\n"
                "• `/gen 4169168384` - BIN de 8 dígitos\n"
                "• `/gen 416916|12|25` - Con fecha\n\n"
                "💡 *Usa PIPE | como separador*",
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