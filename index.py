# index.py
import os
import importlib
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from funcionamiento.tokens import TOKENS

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
                    print(f"✅ Comando cargado: {nombre_comando}")
            except Exception as e:
                print(f"❌ Error cargando {nombre_comando}: {e}")
    
    return comandos

async def manejar_mensajes_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto normales"""
    # Puedes agregar funcionalidad aquí si necesitas procesar mensajes de texto
    pass

async def post_init(application):
    """Función que se ejecuta después de inicializar el bot"""
    print("🤖 Bot iniciado correctamente!")

def main():
    # Cargar comandos automáticamente
    global comandos
    comandos = cargar_comandos()
    
    if not comandos:
        print("⚠️ No se encontraron comandos. Cerrando...")
        return

    # Seleccionamos el primer token
    token = TOKENS["BOT_1"]
    
    # Crear aplicación
    application = Application.builder().token(token).post_init(post_init).build()

    # Registrar comandos automáticamente
    for nombre, funcion in comandos.items():
        application.add_handler(CommandHandler(nombre, funcion))
        print(f"📝 Registrado comando: /{nombre}")

    # Manejo de mensajes de texto normales
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes_texto))

    print("🚀 Iniciando bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
