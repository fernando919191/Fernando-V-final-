# index.py
import os
import importlib
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from funcionamiento.tokens import TOKENS
from funcionamiento.config import PREFIX

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

def main():
    # Cargar comandos automáticamente
    comandos = cargar_comandos()
    
    if not comandos:
        print("⚠️ No se encontraron comandos. Cerrando...")
        return

    # Seleccionamos el primer token
    token = TOKENS["BOT_1"]
    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    # Registrar comandos automáticamente
    for nombre, funcion in comandos.items():
        dp.add_handler(CommandHandler(nombre, funcion))
        print(f"📝 Registrado comando: /{nombre}")

    # Manejo de prefijos personalizados
    def manejar_prefijos(update, context):
        text = update.message.text.lower()
        
        for nombre, funcion in comandos.items():
            if text.startswith(PREFIX + nombre):
                funcion(update, context)
                return

    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_prefijos))

    print("🤖 Bot iniciado correctamente!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
