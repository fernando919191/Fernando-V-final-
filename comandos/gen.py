# comandos/gen.py
import logging
import random
import re
import requests
import csv
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from funcionamiento.licencias import usuario_tiene_licencia_activa
from funcionamiento.usuarios import registrar_usuario
from index import es_administrador

logger = logging.getLogger(__name__)

# Estados para la conversación
BIN_INPUT, CANTIDAD_INPUT = range(2)

# Configuración
CANTIDAD_DEFECTO = 10

# ─────────── FUNCIONES DE GENERACIÓN MEJORADAS ───────────

def procesar_bin_completo(bin_completo: str) -> tuple:
    """
    Procesa un BIN completo con formato: NUMERO|MM|AAAA|CVV
    Soporta x, rnd, y otros placeholders
    """
    try:
        # Dividir en partes
        partes = bin_completo.split('|')
        
        # Si solo hay una parte, es solo el número/BIN
        if len(partes) == 1:
            numero_raw = partes[0]
            numero = generar_numero_tarjeta(numero_raw)
            if numero.startswith("❌"):
                return None, None, None, None, numero
            
            # Generar valores por defecto
            mes = f"{random.randint(1,12):02d}"
            anio = str(random.randint(2025, 2032))
            
            # Determinar CVV basado en tipo de tarjeta
            if numero.startswith("3") and len(numero) == 15:
                cvv = "".join(random.choices("0123456789", k=4))
            else:
                cvv = "".join(random.choices("0123456789", k=3))
            
            return numero, mes, anio, cvv, None
        
        # Formato completo: NUMERO|MM|AAAA|CVV
        elif len(partes) >= 4:
            numero_raw, mes_raw, anio_raw, cvv_raw = partes[:4]
            
            # Procesar número de tarjeta
            numero = generar_numero_tarjeta(numero_raw)
            if numero.startswith("❌"):
                return None, None, None, None, numero
            
            # Procesar mes
            if mes_raw.lower() in ['rnd', 'random', 'rand']:
                mes = f"{random.randint(1,12):02d}"
            elif mes_raw.isdigit() and 1 <= int(mes_raw) <= 12:
                mes = f"{int(mes_raw):02d}"
            elif mes_raw == '':
                mes = f"{random.randint(1,12):02d}"
            else:
                return None, None, None, None, "❌ Mes inválido. Use 01-12, 'rnd' o déjelo vacío"
            
            # Procesar año
            if anio_raw.lower() in ['rnd', 'random', 'rand']:
                anio = str(random.randint(2025, 2032))
            elif anio_raw.isdigit():
                if len(anio_raw) == 2:
                    anio = "20" + anio_raw
                elif len(anio_raw) == 4:
                    anio = anio_raw
                else:
                    return None, None, None, None, "❌ Año inválido. Use 2 o 4 dígitos"
            elif anio_raw == '':
                anio = str(random.randint(2025, 2032))
            else:
                return None, None, None, None, "❌ Año inválido"
            
            # Procesar CVV
            if cvv_raw.lower() in ['rnd', 'random', 'rand']:
                # Determinar longitud del CVV basado en el tipo de tarjeta
                if numero.startswith("3") and len(numero) == 15:
                    cvv = "".join(random.choices("0123456789", k=4))
                else:
                    cvv = "".join(random.choices("0123456789", k=3))
            elif cvv_raw.isdigit() and len(cvv_raw) in [3, 4]:
                cvv = cvv_raw
            elif cvv_raw == '':
                if numero.startswith("3") and len(numero) == 15:
                    cvv = "".join(random.choices("0123456789", k=4))
                else:
                    cvv = "".join(random.choices("0123456789", k=3))
            else:
                return None, None, None, None, "❌ CVV inválido. Use 3-4 dígitos, 'rnd' o déjelo vacío"
            
            return numero, mes, anio, cvv, None
        
        # Formatos intermedios (2-3 partes)
        elif len(partes) == 2:
            # Formato: BIN|MM
            numero_raw, mes_raw = partes
            numero = generar_numero_tarjeta(numero_raw)
            if numero.startswith("❌"):
                return None, None, None, None, numero
            
            # Procesar mes
            if mes_raw.lower() in ['rnd', 'random', 'rand']:
                mes = f"{random.randint(1,12):02d}"
            elif mes_raw.isdigit() and 1 <= int(mes_raw) <= 12:
                mes = f"{int(mes_raw):02d}"
            elif mes_raw == '':
                mes = f"{random.randint(1,12):02d}"
            else:
                return None, None, None, None, "❌ Mes inválido"
            
            # Valores por defecto para año y CVV
            anio = str(random.randint(2025, 2032))
            if numero.startswith("3") and len(numero) == 15:
                cvv = "".join(random.choices("0123456789", k=4))
            else:
                cvv = "".join(random.choices("0123456789", k=3))
            
            return numero, mes, anio, cvv, None
        
        elif len(partes) == 3:
            # Formato: BIN|MM|AAAA
            numero_raw, mes_raw, anio_raw = partes
            numero = generar_numero_tarjeta(numero_raw)
            if numero.startswith("❌"):
                return None, None, None, None, numero
            
            # Procesar mes
            if mes_raw.lower() in ['rnd', 'random', 'rand']:
                mes = f"{random.randint(1,12):02d}"
            elif mes_raw.isdigit() and 1 <= int(mes_raw) <= 12:
                mes = f"{int(mes_raw):02d}"
            elif mes_raw == '':
                mes = f"{random.randint(1,12):02d}"
            else:
                return None, None, None, None, "❌ Mes inválido"
            
            # Procesar año
            if anio_raw.lower() in ['rnd', 'random', 'rand']:
                anio = str(random.randint(2025, 2032))
            elif anio_raw.isdigit():
                if len(anio_raw) == 2:
                    anio = "20" + anio_raw
                elif len(anio_raw) == 4:
                    anio = anio_raw
                else:
                    return None, None, None, None, "❌ Año inválido"
            elif anio_raw == '':
                anio = str(random.randint(2025, 2032))
            else:
                return None, None, None, None, "❌ Año inválido"
            
            # CVV por defecto
            if numero.startswith("3") and len(numero) == 15:
                cvv = "".join(random.choices("0123456789", k=4))
            else:
                cvv = "".join(random.choices("0123456789", k=3))
            
            return numero, mes, anio, cvv, None
        
        else:
            return None, None, None, None, "❌ Formato incorrecto. Use: BIN o BIN|MM|AAAA|CVV"
        
    except Exception as e:
        logger.error(f"Error procesando BIN completo: {e}")
        return None, None, None, None, f"❌ Error procesando el formato: {e}"

def generar_numero_tarjeta(numero_raw: str) -> str:
    """Genera un número de tarjeta válido con soporte para x y rnd"""
    try:
        # Limpiar y normalizar
        numero_limpio = re.sub(r"[-/\s]", "", numero_raw)
        
        # Reemplazar placeholders
        numero_procesado = ""
        for char in numero_limpio:
            if char.lower() in {'x', 'r', 'd'}:
                numero_procesado += random.choice("0123456789")
            elif char.isdigit():
                numero_procesado += char
            else:
                return f"❌ Carácter no válido: {char}"
        
        # Verificar longitud mínima
        if len(numero_procesado) < 6:
            return f"❌ BIN demasiado corto: {len(numero_procesado)} dígitos (mínimo 6)"
        
        # Completar hasta longitud estándar si es necesario
        if len(numero_procesado) < 15:
            # Determinar longitud objetivo basada en el primer dígito
            if numero_procesado.startswith('3'):
                longitud_objetivo = 15  # American Express
            else:
                longitud_objetivo = 16  # Visa, Mastercard, etc.
            
            # Completar con dígitos aleatorios
            while len(numero_procesado) < longitud_objetivo - 1:
                numero_procesado += random.choice("0123456789")
        
        # Aplicar algoritmo de Luhn
        numero_procesado = aplicar_luhn(numero_procesado)
        
        return numero_procesado
        
    except Exception as e:
        logger.error(f"Error generando número de tarjeta: {e}")
        return f"❌ Error generando número: {e}"

def tiene_luhn_valido(numero: str) -> bool:
    """Verifica si un número ya tiene checksum de Luhn válido"""
    return luhn_checksum(numero) == 0

def aplicar_luhn(numero: str) -> str:
    """Aplica algoritmo de Luhn a un número (sin el último dígito)"""
    # Si ya tiene checksum válido, retornar tal cual
    if tiene_luhn_valido(numero):
        return numero
    
    # Si no, calcular nuevo checksum
    base = numero[:-1] if len(numero) in [15, 16] else numero
    
    for i in range(10):
        posible = base + str(i)
        if luhn_checksum(posible) == 0:
            return posible
    
    # Fallback: agregar dígito y recalcular
    base += random.choice("0123456789")
    for i in range(10):
        posible = base + str(i)
        if luhn_checksum(posible) == 0:
            return posible
    
    return base + "0"  # Último recurso

def luhn_checksum(card_number: str) -> int:
    """Calcula el checksum de Luhn para un número de tarjeta"""
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    
    return checksum % 10

def generar_tarjeta_completa(bin_input: str) -> str:
    """Genera una tarjeta completa con soporte para formatos avanzados"""
    try:
        numero, mes, anio, cvv, error = procesar_bin_completo(bin_input)
        if error:
            return error
        
        return f"{numero}|{mes}|{anio}|{cvv}"
    
    except Exception as e:
        logger.error(f"Error generando tarjeta completa: {e}")
        return "❌ Error interno generando la tarjeta."

def info_bin(bin_str: str) -> str:
    """Obtiene información de un BIN desde binlist.net."""
    # Extraer solo los dígitos para la consulta del BIN
    bin_digits = ''.join([c for c in bin_str if c.isdigit()])
    bin6 = bin_digits[:6]
    
    if len(bin6) < 6:
        return "🔎 BIN inválido para consulta."
    
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin6}", 
                        headers={"Accept-Version": "3"}, 
                        timeout=5)
        
        if r.status_code == 200:
            data = r.json()
            banco = data.get("bank", {}).get("name", "Desconocido")
            pais = data.get("country", {}).get("name", "Desconocido")
            marca = data.get("scheme", "").capitalize()
            tipo = data.get("type", "").capitalize()
            
            return (f"🔎 BIN: {bin6}\n🏦 Banco: {banco}\n"
                   f"🌍 País: {pais}\n💳 Marca: {marca}, Tipo: {tipo}")
        
        return f"🔎 BIN: {bin6}\n❌ No se pudo obtener información (Error: {r.status_code})"
    
    except Exception as e:
        logger.error(f"Error en info_bin: {e}")
        return f"🔎 BIN: {bin6}\n❌ Error de conexión con la API"

# ─────────── HANDLERS ───────────

async def gen_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia la conversación para generar tarjetas."""
    user_id = str(update.effective_user.id)
    
    # Verificar licencia
    if not usuario_tiene_licencia_activa(user_id) and not es_administrador(user_id, update.effective_user.username):
        await update.message.reply_text(
            "❌ No tienes una licencia activa.\n\n"
            "Usa /key <clave> para canjear una licencia.\n"
            "Contacta con un administrador si necesitas una clave."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "💳 *Generador de Tarjetas Avanzado*\n\n"
        "Envía el BIN o formato completo:\n\n"
        "📌 *Formatos soportados:*\n"
        "• `510805` - BIN simple (auto-completado)\n"
        "• `5108xxxx` - BIN con placeholders\n"
        "• `510805|08` - BIN + Mes específico\n"
        "• `510805|rnd|2030` - BIN + Mes aleatorio + Año específico\n"
        "• `510805|08|2030|123` - Formato completo\n"
        "• `510805|rnd|rnd|rnd` - Todo aleatorio\n\n"
        "🔧 *Placeholders:*\n"
        "• `x`, `r`, `d` - Dígito aleatorio\n"
        "• `rnd` - Valor aleatorio (mes, año, CVV)\n"
        "• Campos vacíos - Valor aleatorio automático",
        parse_mode="Markdown"
    )
    return BIN_INPUT

async def recibir_bin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el BIN y pregunta por la cantidad."""
    bin_input = update.message.text.strip()
    context.user_data['bin'] = bin_input
    
    # Validación básica
    if not bin_input or len(bin_input) < 4:
        await update.message.reply_text(
            "❌ Input demasiado corto. Mínimo 4 caracteres.\n"
            "Envía un BIN válido:"
        )
        return BIN_INPUT
    
    # Probar si el formato es válido
    test_result = generar_tarjeta_completa(bin_input)
    if test_result.startswith("❌"):
        await update.message.reply_text(
            f"{test_result}\n\nPor favor, envía un BIN válido:"
        )
        return BIN_INPUT
    
    await update.message.reply_text(
        f"✅ Input recibido: `{bin_input}`\n\n"
        "¿Cuántas tarjetas deseas generar? (1-20)\n"
        f"Por defecto: {CANTIDAD_DEFECTO}",
        parse_mode="Markdown"
    )
    return CANTIDAD_INPUT

async def recibir_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la cantidad y genera las tarjetas."""
    try:
        cantidad_texto = update.message.text.strip()
        if cantidad_texto.isdigit():
            cantidad = max(1, min(20, int(cantidad_texto)))  # Máximo 20 por seguridad
        else:
            cantidad = CANTIDAD_DEFECTO
        
        bin_input = context.user_data.get('bin', '')
        
        start_time = time.time()
        
        # Generar tarjetas
        tarjetas = []
        errores = 0
        max_intentos = cantidad * 3  # Límite de intentos
        
        for i in range(max_intentos):
            if len(tarjetas) >= cantidad:
                break
                
            tarjeta = generar_tarjeta_completa(bin_input)
            if not tarjeta.startswith("❌"):
                tarjetas.append(tarjeta)
            else:
                errores += 1
        
        if not tarjetas:
            await update.message.reply_text("❌ No se pudo generar ninguna tarjeta válida.")
            return ConversationHandler.END
        
        # Obtener información del BIN
        bin_info = info_bin(bin_input)
        
        elapsed = time.time() - start_time
        user = update.effective_user
        user_tag = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if user.username:
            user_tag += f" @{user.username}"
        
        # Estilo personalizado
        respuesta = (
            f"⚜️ 𝑰𝒏𝒑𝒖𝒕: \n"
            f"`{bin_input}`\n"
            f"╚━━━━━━「 𝑪𝑪𝒔 ♻️ 」━━━━━━╝\n"
            + "\n".join([f"`{t}`" for t in tarjetas]) +
            f"\n╚━━━━━━「 𝑫𝑬𝑻𝑨𝑰𝑳𝑺 」━━━━━━╝\n"
            f"⚜️ Bin Information:\n{bin_info}\n"
            f"⚜️ 𝑻𝒊𝒎𝒆 𝑺𝒑𝒆𝒏𝒕 -» {elapsed:.3f}'s\n"
            f"⚜️ 𝑮𝒆𝒏𝒆𝒓𝒂𝒕𝒆𝒅 𝑩𝒚: {user_tag}"
        )
        
        if errores > 0:
            respuesta += f"\n⚜️ 𝑬𝒓𝒓𝒐𝒓𝒔: {errores}"
        
        # Dividir si es muy largo
        if len(respuesta) > 4000:
            partes = [respuesta[i:i+4000] for i in range(0, len(respuesta), 4000)]
            for parte in partes:
                await update.message.reply_text(parte, parse_mode="Markdown")
        else:
            await update.message.reply_text(respuesta, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Error en recibir_cantidad: {e}")
        await update.message.reply_text("❌ Error al procesar la cantidad.")
    
    return ConversationHandler.END

async def gen_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela la conversación."""
    await update.message.reply_text("❌ Generación de tarjetas cancelada.")
    return ConversationHandler.END

async def gen_directo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando .gen con parámetros directos."""
    user_id = str(update.effective_user.id)
    
    # Verificar licencia
    if not usuario_tiene_licencia_activa(user_id) and not es_administrador(user_id, update.effective_user.username):
        await update.message.reply_text(
            "❌ No tienes una licencia activa.\n\n"
            "Usa /key <clave> para canjear una licencia.\n"
            "Contacta con un administrador si necesitas una clave."
        )
        return
    
    texto = update.message.text.strip()
    partes = texto.split(maxsplit=2)  # .gen BIN [cantidad]
    
    if len(partes) < 2:
        await update.message.reply_text(
            "💳 *Uso rápido:* `.gen BIN [cantidad]`\n\n"
            "📌 *Ejemplos:*\n"
            "• `.gen 510805` - 10 tarjetas\n"
            "• `.gen 416916 5` - 5 tarjetas\n"
            "• `.gen 5108xxxx` - Con placeholders\n"
            "• `.gen 557910043338xxxx|08|2030|123` - Formato completo\n"
            "• `.gen 510805|rnd|rnd|rnd` - Todo aleatorio\n\n"
            "🔧 *Placeholders:*\n"
            "• `x` - Dígito aleatorio\n"
            "• `rnd` - Valor aleatorio",
            parse_mode="Markdown"
        )
        return
    
    bin_input = partes[1]
    cantidad = CANTIDAD_DEFECTO
    
    if len(partes) > 2 and partes[2].isdigit():
        cantidad = max(1, min(20, int(partes[2])))
    
    start_time = time.time()

    # Generar tarjetas
    tarjetas = []
    errores = 0
    max_intentos = cantidad * 3
    
    for i in range(max_intentos):
        if len(tarjetas) >= cantidad:
            break
            
        tarjeta = generar_tarjeta_completa(bin_input)
        if not tarjeta.startswith("❌"):
            tarjetas.append(tarjeta)
        else:
            errores += 1

    if not tarjetas:
        await update.message.reply_text("❌ No se pudo generar ninguna tarjeta válida.")
        return

    # Obtener información del BIN
    bin_info = info_bin(bin_input)

    elapsed = time.time() - start_time
    user = update.effective_user
    user_tag = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if user.username:
        user_tag += f" @{user.username}"

    # Estilo personalizado
    respuesta = (
        f"⚜️ 𝑰𝒏𝒑𝒖𝒕: \n"
        f"`{bin_input}`\n"
        f"╚━━━━━━「 𝑪𝑪𝒔 ♻️ 」━━━━━━╝\n"
        + "\n".join([f"`{t}`" for t in tarjetas]) +
        f"\n╚━━━━━━「 𝑫𝑬𝑻𝑨𝑰𝑳𝑺 」━━━━━━╝\n"
        f"⚜️ Bin Information:\n{bin_info}\n"
        f"⚜️ 𝑻𝒊𝒎𝒆 𝑺𝒑𝒆𝒏𝒕 -» {elapsed:.3f}'s\n"
        f"⚜️ 𝑮𝒆𝒏𝒆𝒓𝒂𝒕𝒆𝒅 𝑩𝒚: {user_tag}"
    )

    if errores > 0:
        respuesta += f"\n⚜️ 𝑬𝒓𝒓𝒐𝒓𝒔: {errores}"

    if len(respuesta) > 4000:
        partes = [respuesta[i:i+4000] for i in range(0, len(respuesta), 4000)]
        for parte in partes:
            await update.message.reply_text(parte, parse_mode="Markdown")
    else:
        await update.message.reply_text(respuesta, parse_mode="Markdown")

def setup(application):
    """Configura el ConversationHandler para el comando /gen"""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('gen', gen_start)],
        states={
            BIN_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_bin)],
            CANTIDAD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cantidad)],
        },
        fallbacks=[CommandHandler('cancel', gen_cancel)],
    )
    
    # También agregar handler para .gen directo
    application.add_handler(MessageHandler(filters.Regex(r'^\.gen\b'), gen_directo))
    
    return conv_handler

# Handler para el comando tradicional /gen
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wrapper para el comando /gen que inicia la conversación."""

    return await gen_start(update, context)
