# index.py
import os
import importlib
import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.tokens import TOKENS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cargar_comandos():
    """Carga automáticamente todos los comandos de la carpeta 'comandos'"""
    comandos = {}
    ruta_comandos = os.path.join(os.path.dirname(__file__), 'comandos')
    
    if not os.path.exists(ruta_comandos):
        logger.error("❌ Carpeta 'comandos' no encontrada")
        return comandos
    
    for archivo in os.listdir(ruta_comandos):
        if archivo.endswith('.py') and archivo != '__init__.py':
            nombre_comando = archivo[:-3]  # Quita la extensión .py
            try:
                modulo = importlib.import_module(f'comandos.{nombre_comando}')
                if hasattr(modulo, nombre_comando):
                    comandos[nombre_comando] = getattr(modulo, nombre_comando)
                    logger.info(f"✅ Comando cargado: {nombre_comando}")
                else:
                    logger.warning(f"⚠️ Función {nombre_comando} no encontrada en {archivo}")
            except Exception as e:
                logger.error(f"❌ Error cargando {nombre_comando}: {e}")
    
    return comandos

async def eliminar_webhook(token):
    """Elimina cualquier webhook configurado previamente"""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
            )
            if response.status_code == 200:
                logger.info("✅ Webhook eliminado correctamente")
            else:
                logger.warning(f"⚠️ No se pudo eliminar webhook: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error eliminando webhook: {e}")

async def manejar_mensajes_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto normales"""
    try:
        logger.info(f"📩 Mensaje recibido: {update.message.text}")
        await update.message.reply_text("🤖 Escribe /help para ver los comandos disponibles")
    except Exception as e:
        logger.error(f"❌ Error en manejar_mensajes_texto: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores globales"""
    logger.error(f"🚨 Error en update {update}: {context.error}")

def main():
    try:
        logger.info("🚀 Iniciando bot...")
        
        # Cargar comandos automáticamente
        comandos = cargar_comandos()
        
        if not comandos:
            logger.error("⚠️ No se encontraron comandos. Cerrando...")
            return

        # Obtener token
        token = TOKENS["BOT_1"]
        logger.info(f"🔑 Token cargado: {token[:10]}...")
        
        # Eliminar cualquier webhook previo
        asyncio.run(eliminar_webhook(token))
        
        # Crear aplicación
        application = Application.builder().token(token).build()

        # Registrar comandos automáticamente
        for nombre, funcion in comandos.items():
            application.add_handler(CommandHandler(nombre, funcion))
            logger.info(f"📝 Registrado comando: /{nombre}")

        # Manejo de mensajes de texto normales
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes_texto))
        
        # Manejo de errores globales
        application.add_error_handler(error_handler)

        logger.info("🤖 Bot configurado correctamente")
        logger.info(f"📋 Comandos disponibles: {', '.join(['/' + cmd for cmd in comandos.keys()])}")
        
        # Iniciar polling con configuración robusta
        logger.info("🔄 Iniciando polling...")
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
            
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar el bot: {e}", exc_info=True)
        # Intentar cerrar recursos si es posible
        try:
            if 'application' in locals():
                application.stop()
        except:
            pass

if __name__ == "__main__":
    main()