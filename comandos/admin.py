import os

# Ruta al archivo de administradores
ADMINS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'admins.txt')

def cargar_admins():
    """Carga la lista de administradores desde el archivo"""
    try:
        with open(ADMINS_FILE, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []

def guardar_admins(admins):
    """Guarda la lista de administradores en el archivo"""
    with open(ADMINS_FILE, 'w') as f:
        for admin in admins:
            f.write(f"{admin}\n")

async def admin(update, context):
    """Comando para hacer admin a un usuario"""
    user_id = str(update.effective_user.id)
    
    # Verificar si el usuario es el admin principal
    if user_id != "6751216122", "1747560314",:
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    
    # Verificar los argumentos
    if len(context.args) < 1:
        await update.message.reply_text("❌ Uso: /admin <user_id>")
        return
    
    nuevo_admin = context.args[0]
    
    # Verificar si el user_id es válido (solo números)
    if not nuevo_admin.isdigit():
        await update.message.reply_text("❌ El user_id debe contener solo números.")
        return
    
    # Cargar administradores actuales
    admins = cargar_admins()
    
    # Verificar si el usuario ya es admin
    if nuevo_admin in admins:
        await update.message.reply_text("✅ Este usuario ya es administrador.")
        return
    
    # Agregar el nuevo admin
    admins.append(nuevo_admin)
    guardar_admins(admins)
    

    await update.message.reply_text(f"✅ El usuario {nuevo_admin} ahora es administrador.")
