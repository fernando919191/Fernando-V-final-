from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import random
import re
from datetime import datetime

# Esquemas de marcas
CARD_SCHEMES = {
    "visa": {"length": 16, "cvv_len": 3, "prefixes": ["4"]},
    "mastercard": {"length": 16, "cvv_len": 3, "prefixes": ["51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27"]},
    "amex": {"length": 15, "cvv_len": 4, "prefixes": ["34", "37"]},
    "discover": {"length": 16, "cvv_len": 3, "prefixes": ["6011", "65"]},
    "jcb": {"length": 16, "cvv_len": 3, "prefixes": ["35"]},
    "diners": {"length": 16, "cvv_len": 3, "prefixes": ["300", "301", "302", "303", "304", "305", "36", "38"]}
}

# =========================
# Algoritmo Luhn
# =========================
def luhn_checksum(card_number: str) -> int:
    """Calcula el dígito de verificación Luhn"""
    digits = [int(d) for d in card_number]
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return (10 - (total % 10)) % 10

def generate_valid_card(bin_pattern: str, length: int) -> str:
    """Genera un número de tarjeta válido con Luhn, rellenando las 'x'"""
    # Reemplazar todas las 'x' con dígitos aleatorios
    card_without_luhn = ""
    for char in bin_pattern:
        if char.lower() == 'x':
            card_without_luhn += str(random.randint(0, 9))
        else:
            card_without_luhn += char
    
    # Asegurar que no exceda la longitud
    card_without_luhn = card_without_luhn[:length-1]
    
    # Si es más corto, completar con dígitos aleatorios
    remaining_digits = length - 1 - len(card_without_luhn)
    if remaining_digits > 0:
        card_without_luhn += ''.join(str(random.randint(0, 9)) for _ in range(remaining_digits))
    
    # Calcular dígito Luhn
    luhn_digit = luhn_checksum(card_without_luhn + '0')
    
    return card_without_luhn + str(luhn_digit)

# =========================
# Detección de Marca
# =========================
def detect_brand(bin_pattern: str):
    """Detecta la marca basado en los primeros dígitos (ignorando x)"""
    # Extraer solo los dígitos numéricos para detección
    numeric_part = ''.join([c for c in bin_pattern if c.isdigit()])
    if len(numeric_part) < 2:
        return "unknown", 16, 3
    
    for brand, data in CARD_SCHEMES.items():
        for prefix in data["prefixes"]:
            if numeric_part.startswith(prefix):
                return brand, data["length"], data["cvv_len"]
    # Default a Visa/Mastercard si no se detecta
    return "unknown", 16, 3

# =========================
# Handlers
# =========================
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera tarjetas válidas con algoritmo Luhn y soporte para 'x'"""
    try:
        if not context.args:
            await update.message.reply_text(
                "💳 *GENERADOR DE TARJETAS (Luhn + x)*\n\n"
                "📋 *Formato:* `/gen BIN | MM | YY | CVV | CANTIDAD`\n\n"
                "🔧 *Ejemplos:*\n"
                "• `/gen 416916` - 10 tarjetas\n"
                "• `/gen 416916828x771xxx` - Con x aleatorias\n"
                "• `/gen 416916|x|12|25` - Con fecha\n"
                "• `/gen 416916|x|x|123|5` - 5 tarjetas con CVV\n\n"
                "💡 *Características:*\n"
                "- `x` = dígito aleatorio\n"
                "- Luhn válido\n"
                "- Separadores: `|` o `/`",
                parse_mode='Markdown'
            )
            return

        # Parsear parámetros
        text = ' '.join(context.args)
        
        # Convertir separadores a pipe
        if '/' in text:
            text = text.replace('/', '|')
        if '-' in text:
            text = text.replace('-', '|')
        
        params = text.split('|')
        params = [p.strip() for p in params if p.strip()]
        
        if not params:
            await update.message.reply_text("❌ Debes proporcionar un BIN.")
            return
        
        bin_pattern = params[0]
        exp_input = params[1] if len(params) > 1 else None
        cvv_input = params[2] if len(params) > 2 else None
        qty = int(params[3]) if len(params) > 3 and params[3].isdigit() else 10
        qty = max(1, min(qty, 20))
        
        # Validar patrón BIN
        if not any(c.isdigit() or c.lower() == 'x' for c in bin_pattern):
            await update.message.reply_text("❌ Patrón BIN inválido. Debe contener dígitos o 'x'.")
            return
        
        # Detectar marca
        brand, length, cvv_len = detect_brand(bin_pattern)
        
        # Procesar fecha (soporta x en fecha)
        exp_tuple = None
        if exp_input:
            if 'x' in exp_input.lower():
                # Fecha aleatoria si contiene x
                month = f"{random.randint(1, 12):02d}"
                year = str(random.randint(datetime.now().year + 1, datetime.now().year + 5))[2:]
                exp_tuple = (month, f"20{year}")
            elif re.match(r"^(0[1-9]|1[0-2])[/\-]?(\d{2})$", exp_input):
                month = exp_input[:2]
                year_part = exp_input[-2:]
                exp_tuple = (month, f"20{year_part}")
            else:
                await update.message.reply_text("❌ Formato de fecha inválido. Usa: MM/YY o MMx")
                return
        
        # Procesar CVV (soporta x en CVV)
        final_cvv = None
        if cvv_input:
            if 'x' in cvv_input.lower():
                # CVV aleatorio si contiene x
                final_cvv = ''.join(str(random.randint(0, 9)) for _ in range(cvv_len))
            elif cvv_input.isdigit() and len(cvv_input) == cvv_len:
                final_cvv = cvv_input
            else:
                await update.message.reply_text(f"❌ CVV debe tener {cvv_len} dígitos o 'x'.")
                return
        
        # Generar tarjetas
        cards = []
        for _ in range(qty):
            card_number = generate_valid_card(bin_pattern, length)
            
            # Fecha de expiración
            if exp_tuple:
                month, year = exp_tuple
            else:
                month = f"{random.randint(1, 12):02d}"
                year = str(random.randint(datetime.now().year + 1, datetime.now().year + 5))
            
            # CVV
            if final_cvv:
                cvv = final_cvv
            else:
                cvv = ''.join(str(random.randint(0, 9)) for _ in range(cvv_len))
            
            cards.append(f"{card_number}|{month}|{year}|{cvv}")
        
        # Enviar resultados
        response = f"💳 *{len(cards)} tarjeta(s) generada(s):*\n```\n" + "\n".join(cards) + "\n```"
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# =========================
# Registro del comando
# =========================
def setup(app):
    """Registra el comando"""
    return CommandHandler("gen", gen)