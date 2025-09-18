# index.py
import os
import importlib
import logging
from functools import wraps

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes

from funcionamiento.tokens import TOKENS
from funcionamiento.licencias import usuario_tiene_licencia_activa
from funcionamiento.licencias import canjear_licencia, obtener_tiempo_restante_licencia
from funcionamiento.usuarios import registrar_usuario

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# -------------------------
# Config Admin
# -------------------------
ADMIN_PRINCIPAL = "6751216122"
ADMINISTRADORES = {
    "6751216122",
    "1747560314",
    "2137906400",
    "8004542002",
    "7446022085",
    "5332276035",
    # Agrega más admins aquí
}

# Cache de comandos
COMANDOS_CARGADOS = None

# -------------------------
# Configuración de permisos
# -------------------------
COMANDOS_SOLO_ADMIN = {
    "addkeys",    # Agregar claves
    "users",      # Listar usuarios  
    "premium",    # Gestión premium
    "remove",     # Remover premium
    "info",
    "genkey",              # Info de usuario (SOLO ADMIN)
    # Agrega aquí más comandos solo para admins
}

COMANDOS_SIN_LICENCIA = {
    "key",        # Canjear licencia
    "start",      # Comando inicial
    "help",       # Ayuda
    "me",         # Información personal básica
    "ping",       # Test de conexión
    # Agrega aquí comandos públicos que no requieran licencia
}


def es_administrador(user_id: str, username: str | None = None) -> bool:
    """Verifica si un usuario es administrador."""
    user_id_str = str(user_id)
    username_str = f"@{username.lower()}" if username else ""
    return (
        user_id_str in ADMINISTRADORES
        or username_str in ADMINISTRADORES
        or user_id_str == ADMIN_PRINCIPAL
    )


def comando_con_licencia(func):
    """Decorador para verificar licencia y permisos antes de ejecutar un comando."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if update.effective_user is None:
                return

            user_id = str(update.effective_user.id)
            username = update.effective_user.username
            first_name = update.effective_user.first_name
            last_name = update.effective_user.last_name
            command_name = func.__name__

            # Registrar usuario siempre
            registrar_usuario(user_id, username, first_name, last_name)

            # Admins: sin verificación de licencia
            if es_administrador(user_id, username):
                return await func(update, context)

            # Comandos que solo admins pueden usar
            if command_name in COMANDOS_SOLO_ADMIN:
                await update.message.reply_text("❌ No tienes permisos para usar este comando.")
                return

            # Comandos que no requieren licencia
            if command_name in COMANDOS_SIN_LICENCIA:
                return await func(update, context)

            # Comandos que requieren licencia
            if not usuario_tiene_licencia_activa(user_id):
                await update.message.reply_text(
                    "❌ No tienes una licencia activa.\n\n"
                    "Usa /key <clave> para canjear una licencia.\n"
                    "Contacta con un administrador si necesitas una clave."
                )
                return

            return await func(update, context)

        except Exception as e:
            logger.error(f"❌ Error en wrapper de comando '{func.__name__}': {e}", exc_info=True)

    return wrapper


def _obtener_funcion_comando(modulo, nombre_archivo: str):
    """
    Intenta obtener la función manejadora del módulo con estas prioridades:
    1) async def <nombre_archivo>(update, context)
    2) async def handle(update, context)
    3) COMMAND (callable)
    """
    func = getattr(modulo, nombre_archivo, None)
    if callable(func):
        return func
    func = getattr(modulo, "handle", None)
    if callable(func):
        return func
    func = getattr(modulo, "COMMAND", None)
    if callable(func):
        return func
    return None


def cargar_comandos():
    """Carga automáticamente todos los comandos de la carpeta 'comandos'."""
    global COMANDOS_CARGADOS
    if COMANDOS_CARGADOS is not None:
        return COMANDOS_CARGADOS

    comandos = {}
    ruta_comandos = os.path.join(os.path.dirname(__file__), "comandos")

    if not os.path.exists(ruta_comandos):
        logger.error("❌ Carpeta 'comandos' no encontrada")
        COMANDOS_CARGADOS = {}
        return COMANDOS_CARGADOS

    for archivo in os.listdir(ruta_comandos):
        if not (archivo.endswith(".py") and archivo != "__init__.py"):
            continue

        nombre = archivo[:-3]
        try:
            # Import relativo para evitar problemas de CWD
            modulo = importlib.import_module(f".{nombre}", package="comandos")
            func = _obtener_funcion_comando(modulo, nombre)

            if callable(func):
                comandos[nombre] = comando_con_licencia(func)
                logger.info(f"✅ Comando cargado: /{nombre}")
            else:
                logger.warning(
                    f"⚠️ No se encontró función para '{nombre}'. "
                    f"Define '{nombre}()' or 'handle()' or 'COMMAND'."
                )
        except Exception as e:
            logger.error(f"❌ Error cargando comando '{nombre}': {e}", exc_info=True)

    COMANDOS_CARGADOS = comandos
    return comandos


def cargar_comandos_conversacion(application: Application):
    """Carga comandos que usan ConversationHandler mediante una función setup(application)."""
    ruta_comandos = os.path.join(os.path.dirname(__file__), "comandos")
    if not os.path.exists(ruta_comandos):
        return

    for archivo in os.listdir(ruta_comandos):
        if not (archivo.endswith(".py") and archivo != "__init__.py"):
            continue

        nombre = archivo[:-3]
        try:
            modulo = importlib.import_module(f".{nombre}", package="comandos")
            if hasattr(modulo, "setup"):
                handler = modulo.setup(application)
                application.add_handler(handler)
                logger.info(f"✅ Comando de conversación cargado: /{nombre}")
        except Exception as e:
            logger.error(f"❌ Error cargando conversación '{nombre}': {e}", exc_info=True)


def eliminar_webhook_sincrono(token: str):
    """Elimina webhook de forma síncrona para asegurar polling limpio."""
    import requests

    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true",
            timeout=10,
        )
        if resp.status == 200:
            logger.info("✅ Webhook eliminado correctamente")
        else:
            logger.warning(f"⚠️ No se pudo eliminar webhook: {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ Error eliminando webhook: {e}")


async def manejar_todos_los_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja TODOS los mensajes de texto que NO son comandos /slash y soporta .comandos."""
    try:
        if update.effective_user is None:
            return
        if update.message is None or update.message.text is None:
            return  # ignorar stickers, fotos, etc.

        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        message_text = update.message.text.strip()

        # Registrar al usuario siempre
        registrar_usuario(user_id, username, first_name, last_name)
        logger.info(f"📩 Mensaje recibido: {message_text}")

        # Comandos con punto: .comando arg1 arg2 ...
        if message_text.startswith("."):
            partes = message_text[1:].split()
            if not partes:
                return

            comando = partes[0].lower()
            args = partes[1:] if len(partes) > 1 else []
            logger.info(f"🔍 Comando con punto detectado: .{comando}, args: {args}")

            comandos_disponibles = COMANDOS_CARGADOS or cargar_comandos()

            if comando in comandos_disponibles:
                # VERIFICAR PERMISOS PARA COMANDOS CON PUNTO
                if not es_administrador(user_id, username):
                    # Comandos que solo admins pueden usar
                    if comando in COMANDOS_SOLO_ADMIN:
                        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
                        return
                    
                    # Comandos que requieren licencia
                    if (comando not in COMANDOS_SIN_LICENCIA and 
                        not usuario_tiene_licencia_activa(user_id)):
                        await update.message.reply_text(
                            "❌ No tienes una licencia activa.\n\n"
                            "Usa /key <clave> para canjear una licencia.\n"
                            "Contacta con un administrador si necesitas una clave."
                        )
                        return
                
                logger.info(f"✅ Ejecutando comando: .{comando}")
                context.args = args  # simular args para handlers
                await comandos_disponibles[comando](update, context)
                return
            else:
                await update.message.reply_text(f"❌ Comando '.{comando}' no reconocido")
                return

        # MENSAJES NORMALES (NO COMANDOS): NO EXIGIR LICENCIA
        # Los usuarios pueden chatear normalmente sin licencia

    except Exception as e:
        logger.error(f"❌ Error en manejar_todos_los_mensajes: {e}", exc_info=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Manejador global de errores."""
    logger.error(f"🚨 Error en update {update}: {context.error}", exc_info=True)


def main():
    try:
        logger.info("🚀 Iniciando bot...")

        # Cargar comandos una sola vez
        comandos = cargar_comandos()
        if not comandos:
            logger.error("⚠️ No se encontraron comandos. Cerrando...")
            return

        # Token
        token = TOKENS["BOT_1"]
        logger.info(f"🔑 Token cargado: {token[:10]}...")

        # Asegurar polling limpio
        eliminar_webhook_sincrono(token)

        # App Telegram
        application = Application.builder().token(token).build()

        # Registrar comandos /slash
        for nombre, funcion in comandos.items():
            application.add_handler(CommandHandler(nombre, funcion))
            logger.info(f"📝 Registrado comando: /{nombre}")

        # Registrar callback handler para tmp
        try:
            from comandos.tmp import handle_callback
            application.add_handler(CallbackQueryHandler(handle_callback, pattern="^tmp_"))
            logger.info("✅ Callback handler para tmp registrado")
        except ImportError as e:
            logger.warning(f"⚠️ No se pudo cargar callback handler para tmp: {e}")
        except Exception as e:
            logger.error(f"❌ Error registrando callback handler: {e}")

        # Cargar ConversationHandlers (si los hay)
        cargar_comandos_conversacion(application)

        # Handler de texto que NO capture /comandos
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_todos_los_mensajes)
        )

        # Errores globales
        application.add_error_handler(error_handler)

        logger.info("🤖 Bot configurado correctamente")
        logger.info(f"👑 Administradores: {ADMINISTRADORES}")
        logger.info(f"🔐 Comandos solo admin: {COMANDOS_SOLO_ADMIN}")
        logger.info(f"🔓 Comandos sin licencia: {COMANDOS_SIN_LICENCIA}")

        lista = list(comandos.keys())
        logger.info("📋 Comandos disponibles /: " + ", ".join("/" + c for c in lista))
        logger.info("📋 Comandos disponibles .: " + ", ".join("." + c for c in lista))

        # Polling
        logger.info("🔄 Iniciando polling...")
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
        )

    except Exception as e:
        logger.error(f"❌ Error crítico: {e}", exc_info=True)


if __name__ == "__main__":
    main()
