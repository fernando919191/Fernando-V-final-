# index.py
import os
import importlib
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.tokens import TOKENS
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cargar_comandos():
    """Carga automáticamente todos los comandos de la carpeta 'comandos'"""
    comandos = {}
    ruta_comandos = os.path.join(os.path.dirname(__file__), 'comandos')
    
    for archivo in os.listdir(ruta_comandos):
        if archivo.endswith('.py') and archivo != '__init__.py':
            nombre_comando = archivo[:-3]  # Quita la extensión .py
            try:
                modulo = importlib.import_module(f'comandos.{nombre_comando}')
                if hasattr(modulo, nombre_comando):
                    comandos[nombre_comando] = getattr(modulo, nombre_comando)
                    logger.info(f"✅ Comando cargado: {nombre_comando}")
            except Exception as e:
                logger.error(f"❌ Error cargando {nombre_comando}: {e}")
    
    return comandos

async def manejar_mensajes_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto normales"""
    logger.info(f"Mensaje recibido: {update.message.text}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores"""
    logger.error(f"Error: {context.error}")

def main():
    try:
        # Cargar comandos automáticamente
        comandos = cargar_comandos()
        
        if not comandos:
            logger.error("⚠️ No se encontraron comandos. Cerrando...")
            return

        # Seleccionamos el primer token
        token = TOKENS["BOT_1"]
        
        # Crear aplicación
        application = Application.builder().token(token).build()

        # Registrar comandos automáticamente
        for nombre, funcion in comandos.items():
            application.add_handler(CommandHandler(nombre, funcion))
            logger.info(f"📝 Registrado comando: /{nombre}")

        # Manejo de mensajes de texto normales
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes_texto))
        
        # Manejo de errores
        application.add_error_handler(error_handler)

        logger.info("🚀 Iniciando bot con webhook...")
        
        # Configurar para Discloud
        PORT = int(os.environ.get('PORT', 8080))
        
        # Usar polling para desarrollo o webhook para producción
        if os.environ.get('DISCLOUD_APP'):
            # Modo Discloud (webhook)
            WEBHOOK_URL = f"https://your-app-name.discloudbot.com"  # 🔄 Cambia esto
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=WEBHOOK_URL
            )
        else:
            # Modo local (polling)
            application.run_polling(drop_pending_updates=True)
            
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    main()
