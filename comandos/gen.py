import random
import re
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

# Estados del flujo
STATE_BIN, STATE_EXP, STATE_CVV = range(3)

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
    """
    Acepta:
      - 'skip' / 'aleatorio' / 'random' / 's' -> None (aleatorio)
      - 'MM/YY'  -> retorna ('MM', 'YYYY')
      - 'MM/YYYY'-> retorna ('MM', 'YYYY')
    """
    t = txt.strip().lower()
    if t in ["skip", "aleatorio", "random", "s", ""]:
        return None

    m = re.match(r"^(0[1-9]|1[0-2])/(?:\d{2}|\d{4})$", t)
    if not m:
        return "ERROR"

    month = t.split("/")[0]
    year_part = t.split("/")[1]
    if len(year_part) == 2:
        # Normalizamos a 4 dígitos (asumimos 2000-2099)
        year4 = f"20{year_part}"
    else:
        year4 = year_part
    return (month, year4)

def generate_cards(bin_prefix: str, qty: int, exp_tuple, cvv_input: str | None):
    brand, length, cvv_len = detect_brand(bin_prefix)
    rem = length - len(bin_prefix) - 1
    cards = []
    for _ in range(qty):
        middle = ''.join(str(random.randint(0, 9)) for _ in range(rem))
        partial = int(bin_prefix + middle)
        number = bin_prefix + middle + str(calculate_luhn(partial))

        # Expiración
        if exp_tuple is None:
            month = f"{random.randint(1,12):02d}"
            year4 = str(random.randint(datetime.now().year + 1, datetime.now().year + 5))
        else:
            month, year4 = exp_tuple  # ya viene normalizado a YYYY

        # CVV
        if cvv_input:
            cvv = cvv_input
        else:
            cvv = ''.join(str(random.randint(0, 9)) for _ in range(cvv_len))

        # Salida en formato NUM|MM|YYYY|CVV
        cards.append(f"{number}|{month}|{year4}|{cvv}")

    return cards, cvv_len

# =========================
# Handlers de Telegram
# =========================
async def gen(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de generación de tarjetas"""
    # Verificar licencia primero (esto se maneja automáticamente por el decorador)
    await update.message.reply_text("💳 **Generador de Tarjetas**\n\nEnvía un BIN (6-8 dígitos) para comenzar.")
    return STATE_BIN

async def bin_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    binp = update.message.text.strip()
    if not binp.isdigit():
        return await update.message.reply_text("❌ El BIN debe contener solo dígitos. Intenta de nuevo.")
    
    if len(binp) < 6 or len(binp) > 8:
        return await update.message.reply_text("❌ El BIN debe tener entre 6 y 8 dígitos. Intenta de nuevo.")
    
    brand, length, cvv_len = detect_brand(binp)
    if not brand:
        return await update.message.reply_text("❌ BIN desconocido. Prueba con un BIN válido.")
    
    ctx.user_data['bin'] = binp
    ctx.user_data['cvv_len'] = cvv_len
    
    await update.message.reply_text(
        f"✅ **Marca detectada:** {brand.upper()}\n"
        f"📏 **Dígitos:** {length}\n"
        f"🔢 **CVV:** {cvv_len} dígitos\n\n"
        "📅 Ingresa fecha de expiración (MM/YY o MM/YYYY) o escribe 'skip' para aleatoria."
    )
    return STATE_EXP

async def exp_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    parsed = parse_exp_input(update.message.text)
    if parsed == "ERROR":
        return await update.message.reply_text("❌ Formato inválido. Usa MM/YY o MM/YYYY, o escribe 'skip'.")
    
    ctx.user_data['exp'] = parsed  # None o (MM, YYYY)
    cvv_len = ctx.user_data.get('cvv_len', 3)
    
    await update.message.reply_text(
        f"🔢 Ingresa CVV ({cvv_len} dígitos) o escribe 'skip' para aleatorio."
    )
    return STATE_CVV

async def cvv_received(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    cvv_len = ctx.user_data.get('cvv_len', 3)
    
    if txt in ["skip", "aleatorio", "random", "s", ""]:
        cvv_value = None
    else:
        if not re.fullmatch(r"\d{" + str(cvv_len) + r"}", txt):
            return await update.message.reply_text(f"❌ El CVV debe tener {cvv_len} dígitos o escribe 'skip'.")
        cvv_value = txt

    ctx.user_data['cvv'] = cvv_value
    data = ctx.user_data
    
    # Generar 10 tarjetas (cantidad fija)
    cards, _ = generate_cards(data['bin'], 10, data['exp'], data['cvv'])
    
    # Enviar las tarjetas generadas
    resultado = "💳 **Tarjetas Generadas:**\n\n" + "\n".join(cards)
    
    # Dividir el mensaje si es muy largo (límite de Telegram: 4096 caracteres)
    if len(resultado) > 4000:
        partes = [resultado[i:i+4000] for i in range(0, len(resultado), 4000)]
        for parte in partes:
            await update.message.reply_text(parte)
    else:
        await update.message.reply_text(resultado)
    
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

def setup(application):
    """Configura el ConversationHandler para el comando /gen"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("gen", gen)],
        states={
            STATE_BIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bin_received)],
            STATE_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, exp_received)],
            STATE_CVV: [MessageHandler(filters.TEXT & ~filters.COMMAND, cvv_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    return conv_handler