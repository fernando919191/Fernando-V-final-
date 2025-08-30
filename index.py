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

# ID de usuario administrador principal
ADMIN_PRINCIPAL = "6751216122"

# Importar funciones después de definir constantes para evitar circular imports
from funcionamiento.licencias import usuario_tiene_licencia_activa
from funcionamiento.usuarios import registrar_usuario
from funcionamiento.alpha_bridge import parsear_respuesta_alpha, mensajes_pendientes

def comando_con_licencia(func):
    """Decorador para verificar licencia antes de ejecutar un comando"""
    async def wrapper(update, context):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        command_name = func.__name__
        
        # Registrar al usuario en la base de datos (SIEMPRE se registra)
        registrar_usuario(user_id, username, first_name, last_name)
        
        # Permitir siempre estos comandos sin verificación de licencia
        comandos_permitidos_sin_licencia = ['key', 'start', 'addkeys', 'help', 'users', 'me', 'ppconfig']
        
        if command_name not in comandos_permitidos_sin_licencia and not usuario_tiene_licencia_activa(user_id):
            await update.message.reply_text(
                "❌ No tienes una licencia activa.\n\n"
                "Usa /key <clave> para canjear una licencia.\n"
                "Contacta con un administrador si necesitas una clave."
            )
            return
        
        # Verificación especial para addkeys - solo el admin principal puede usarlo
        if command_name == 'addkeys' and user_id != ADMIN_PRINCIPAL:
            await update.message.reply_text("❌ No tienes permisos para usar este comando.")
            return
        
        # Verificación especial para users - solo el admin principal puede usarlo
        if command_name == 'users' and user_id != ADMIN_PRINCIPAL:
            await update.message.reply_text("❌ No tienes permisos para usar este comando.")
            return
        
        # Si tiene licencia o es un comando permitido, ejecutar la función
        return await func(update, context)
    
    return wrapper

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
                    # Aplicar el decorador de verificación de licencia
                    funcion_original = getattr(modulo, nombre_comando)
                    funcion_con_licencia = comando_con_licencia(funcion_original)
                    comandos[nombre_comando] = funcion_con_licencia
                    logger.info(f"✅ Comando cargado: {nombre_comando} (con verificación de licencia)")
                else:
                    logger.warning(f"⚠️ Función {nombre_comando} no encontrada en {archivo}")
            except Exception as e:
                logger.error(f"❌ Error cargando {nombre_comando}: {e}")
    
    return comandos

def cargar_comandos_conversacion(application):
    """Carga comandos que necesitan ConversationHandler"""
    ruta_comandos = os.path.join(os.path.dirname(__file__), 'comandos')
    
    if not os.path.exists(ruta_comandos):
        return
    
    for archivo in os.listdir(ruta_comandos):
        if archivo.endswith('.py') and archivo != '__init__.py':
            nombre_comando = archivo[:-3]
            try:
                modulo = importlib.import_module(f'comandos.{nombre_comando}')
                # SOLO para comandos que realmente necesitan ConversationHandler
                if hasattr(modulo, 'setup') and nombre_comando == 'gen':  # Solo /gen
                    handler = modulo.setup(application)
                    application.add_handler(handler)
                    logger.info(f"✅ Comando conversación cargado: /{nombre_comando}")
            except Exception as e:
                logger.error(f"❌ Error cargando comando {nombre_comando}: {e}")

def eliminar_webhook_sincrono(token):
    """Elimina webhook de forma síncrona (sin asyncio)"""
    import requests
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        )
        if response.status_code == 200:
            logger.info("✅ Webhook eliminado correctamente")
        else:
            logger.warning(f"⚠️ No se pudo eliminar webhook: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error eliminando webhook: {e}")

async def manejar_mensajes_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto normales con verificación de licencia"""
    try:
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name
        message_text = update.message.text
        
        # Registrar al usuario en la base de datos (SIEMPRE se registra)
        registrar_usuario(user_id, username, first_name, last_name)
        
        logger.info(f"📩 Mensaje recibido de {user_id}: {message_text}")
        
        # Verificar si el usuario tiene licencia activa
        if not usuario_tiene_licencia_activa(user_id):
            # Permitir solo los comandos esenciales sin licencia
            comandos_permitidos = ['/key', '/start', '/addkeys', '/help', '/users', '/me', '/ppconfig', '/bn']
            if any(message_text.startswith(cmd) for cmd in comandos_permitidos):
                # Permitir que estos comandos se procesen normalmente
                return
            else:
                # Bloquear otros mensajes si no tiene licencia
                await update.message.reply_text(
                    "❌ No tienes una licencia activa.\n\n"
                    "Usa /key <clave> para canjear una licencia.\n"
                    "Contacta con un administrador si necesitas una clave."
                )
                return
        
        # Si tiene licencia, procesar el mensaje normalmente
        
    except Exception as e:
        logger.error(f"❌ Error en manejar_mensajes_texto: {e}")

async def manejar_respuestas_alpha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura respuestas de @Alphachekerbot"""
    try:
        # Verificar si es mensaje de @Alphachekerbot
        if (update.message and update.message.from_user and 
            update.message.from_user.username and 
            'alphachekerbot' in update.message.from_user.username.lower()):
            
            logger.info(f"📩 Mensaje de Alpha recibido: {update.message.text}")
            
            # Parsear respuesta
            datos = parsear_respuesta_alpha(update.message.text)
            if not datos:
                return
            
            # Buscar mensaje original
            for msg_id, info in list(mensajes_pendientes.items()):
                if info['cc_data'] in update.message.text:
                    # Enviar respuesta formateada al usuario
                    respuesta = f"""
✅ **Respuesta de Alpha Checker**

💳 **CC:** `{datos['cc']}`
📊 **Status:** {datos['status']}
📝 **Response:** {datos['response']}
🏦 **Bank:** {datos['bank']}
🇵 **Country:** {datos['country']}
🔢 **Type:** {datos['type']}
🔍 **BIN:** {datos['bin']}

⏰ Procesado por @HellOfficial1_bot
                    """
                    
                    await context.bot.send_message(
                        chat_id=info['chat_id'],
                        text=respuesta,
                        parse_mode='Markdown'
                    )
                    
                    # Eliminar de pendientes
                    del mensajes_pendientes[msg_id]
                    logger.info(f"✅ Respuesta enviada al usuario {info['chat_id']}")
                    break
                    
    except Exception as e:
        logger.error(f"❌ Error manejando respuesta Alpha: {e}")

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
        
        # Eliminar webhook de forma SÍNCRONA (evita problemas de event loop)
        eliminar_webhook_sincrono(token)
        
        # Crear aplicación
        application = Application.builder().token(token).build()

        # Registrar comandos automáticamente
        for nombre, funcion in comandos.items():
            application.add_handler(CommandHandler(nombre, funcion))
            logger.info(f"📝 Registrado comando: /{nombre}")

        # Registrar comandos de conversación (como /gen)
        cargar_comandos_conversacion(application)

        # Manejo de mensajes de texto normales (con verificación de licencia)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes_texto))
        
        # Manejo de respuestas de @Alphachekerbot
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_respuestas_alpha))
        
        # Manejo de errores globales
        application.add_error_handler(error_handler)

        logger.info("🤖 Bot configurado correctamente")
        
        # Obtener lista de comandos registrados
        todos_comandos = list(comandos.keys())
        # Agregar comandos de conversación
        if os.path.exists(os.path.join('comandos', 'gen.py')):
            todos_comandos.append('gen')
        if os.path.exists(os.path.join('comandos', 'bn.py')):
            todos_comandos.append('bn')
        
        logger.info(f"📋 Comandos disponibles: {', '.join(['/' + cmd for cmd in todos_comandos])}")
        
        # Iniciar polling - FORMA CORRECTA para el event loop
        logger.info("🔄 Iniciando polling...")
        
        # Ejecutar en el event loop apropiado
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.start())
            loop.run_until_complete(application.updater.start_polling(
                poll_interval=1.0,
                timeout=30,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            ))
            logger.info("✅ Bot ejecutándose correctamente")
            loop.run_forever()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Deteniendo bot...")
        finally:
            loop.run_until_complete(application.stop())
            loop.run_until_complete(application.shutdown())
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar el bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()