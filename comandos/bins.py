# index.py
import os
import importlib
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.tokens import TOKENS
import logging
import asyncio

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cargar_comandos():
    """Carga automáticamente todos los comandos"""
    comandos = {}
    ruta_comandos = os.path.join(os.path.dirname(__file__), 'comandos')
    
    for archivo in os.listdir(ruta_comandos):
        if archivo.endswith('.py') and archivo != '__init__.py':
            nombre_comando = archivo[:-3]
            try:
                modulo = importlib.import_module(f'comandos.{nombre_comando}')
                if hasattr(modulo, nombre_comando):
                    comandos[nombre_comando] = getattr(modulo, nombre_comando)
                    logger.info(f"✅ Comando cargado: {nombre_comando}")
            except Exception as e:
                logger.error(f"❌ Error cargando {nombre_comando}: {e}")
    
    return comandos

async def eliminar_webhook(token):
    """Elimina cualquier webhook configurado"""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{token}/deleteWebhook"
            )
            if response.status_code == 200:
                logger.info("✅ Webhook eliminado correctamente")
            else:
                logger.warning("⚠️ No se pudo eliminar webhook")
    except Exception as e:
        logger.error(f"❌ Error eliminando webhook: {e}")

async def manejar_mensajes_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto normales"""
    logger.info(f"Mensaje recibido: {update.message.text}")
    await update.message.reply_text("🤖 Bot funcionando en modo polling")

def main():
    try:
        # Cargar comandos
        comandos = cargar_comandos()
        
        if not comandos:
            logger.error("⚠️ No se encontraron comandos")
            return

        # Obtener token
        token = TOKENS["BOT_1"]
        
        # ELIMINAR CUALQUIER WEBHOOK CONFIGURADO
        asyncio.run(eliminar_webhook(token))
        
        # Crear aplicación
        application = Application.builder().token(token).build()

        # Registrar comandos
        for nombre, funcion in comandos.items():
            application.add_handler(CommandHandler(nombre, funcion))
            logger.info(f"📝 Registrado comando: /{nombre}")

        # Manejo de mensajes de texto
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes_texto))

        logger.info("🚀 INICIANDO BOT EN MODO POLLING...")
        logger.info("📋 Comandos disponibles: " + ", ".join([f"/{cmd}" for cmd in comandos.keys()]))
        
        # INICIAR POLLING CON CONFIGURACIÓN ROBUSTA
        application.run_polling(
            poll_interval=1.0,
            timeout=25,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
            
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}", exc_info=True)

if __name__ == "__main__":
    main()