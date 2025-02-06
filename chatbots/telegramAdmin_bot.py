import logging
from telegram import (
    Update, 
    KeyboardButton, 
    ReplyKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler
)
from telegram.ext import CallbackContext
from decouple import config
from asgiref.sync import sync_to_async
import os
import sys
import django

# Agrega la raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configura Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hello_world.settings")  # Reemplaza "myproject" con el nombre real de tu proyecto
django.setup()

# Importa los modelos de Django
from chatbots.models import UserAdmin
from chatbots.models import User
from django.core.exceptions import ObjectDoesNotExist

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Mantener un historial de la conversación para usar en las respuestas
user_conversations = {}
# Diccionario para almacenar el estado del registro
user_registration = {}

### --- Comando /start: Solicitar número de teléfono --- ###
async def start(update: Update, context: CallbackContext):
    # Crear un botón para enviar el número
    contact_button = KeyboardButton("Iniciar Sesión", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)

    # Enviar mensaje con el botón
    await update.message.reply_text("¡Hola! Por favor, comparte tu número de teléfono para continuar.", reply_markup=reply_markup)

### --- Manejador de mensajes de texto --- ###
async def echo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_message = update.message.text

    await update.message.reply_text(f"En Construcción: {user_message}, User ID: {user_id}")

### --- Manejo de contacto (verifica si es cliente o no) --- ###
async def handle_contact(update: Update, context: CallbackContext):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        user_id = update.message.from_user.id

        # Verificar si el número está en la base de datos
        client = await buscar_en_base_de_datos(phone_number)

        if client:
            # Si el usuario es Administrador
            await update.message.reply_text(f"✅ El número {phone_number} es un Administrador.")

            # Si no tiene un telegram_id, registrarlo
            if not client.telegram_id: 
                resp = await registrar_admin(phone_number, user_id)
                if resp:
                    await update.message.reply_text(f"✅ Administrador registrado con éxito.")

            # Enviar opciones de botones si es Administrador
            keyboard = [
                [InlineKeyboardButton("📋 Agregar Usuario", callback_data="add_client")],
                [InlineKeyboardButton("📋 Eliminar Usuario", callback_data="delete_client")],
                [InlineKeyboardButton("⚙️ Configuración", callback_data="configuracion")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Seleccione una opción:", reply_markup=reply_markup)

        else:
            # Si el usuario NO está en la base de datos, ofrecerle registro
            keyboard = [[InlineKeyboardButton("📝 Registrarme", callback_data="registro")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"❌ El número {phone_number} NO es un Administrador. ¿Quieres registrarte?", reply_markup=reply_markup)
    
    else:
        await update.message.reply_text("❌ No se ha recibido un número de teléfono válido.")

### --- Manejador de botones (responder según la opción seleccionada) --- ###
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "add_client":
        user_registration[query.from_user.id] = {"step": "phone"}
        await query.edit_message_text(text="📞 Por favor, ingresa el número de teléfono del usuario:")
    
    elif query.data == "configuracion":
        await query.edit_message_text(text="⚙️ Configuración abierta...")

    elif query.data == "delete_client":
        user_registration[query.from_user.id] = {"step": "delete_phone"}
        await query.edit_message_text(text="📞 Por favor, ingresa el número de teléfono del usuario:")
    
    elif query.data == "registro":
        await query.edit_message_text(text="📝 Para registrarte, por favor contacta con un Administrador.")
        
async def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_message = update.message.text
    
    if user_id in user_registration:
        step = user_registration[user_id]["step"]
        
        if step == "phone":
            user_registration[user_id]["phone"] = user_message
            user_registration[user_id]["step"] = "name"
            await update.message.reply_text("✍️ Ahora, ingresa el nombre del usuario:")
        
        elif step == "name":
            user_registration[user_id]["name"] = user_message
            phone = user_registration[user_id]["phone"]
            name = user_registration[user_id]["name"]
            
            # Guardar en la base de datos
            success = await registrar_usuario(phone, name)
            if success:
                await update.message.reply_text(f"✅ Usuario {name} registrado con éxito.")
            else:
                await update.message.reply_text("❌ Hubo un error al registrar el usuario.")
            
            # Eliminar el registro temporal
            del user_registration[user_id]
        if step == "delete_phone":
            user_registration[user_id]["delete_phone"] = user_message
          
            # Guardar en la base de datos
            success = await eliminar_usuario(user_message)
            if success:
                await update.message.reply_text(f"✅ Usuario eliminado con éxito.")
            else:
                await update.message.reply_text("❌ Hubo un error al eliminar el usuario.")
            
            # Eliminar el registro temporal
            del user_registration[user_id]
    else:
        await update.message.reply_text(f"En Construcción: {user_message}, User ID: {user_id}")

@sync_to_async
def registrar_usuario(phone, name):
    try:
        User.objects.create(phone=phone, name=name)
        return True
    except:
        return False

@sync_to_async
def eliminar_usuario(phone):
    try:
        usuario=User.objects.get(phone=phone)
        usuario.delete()
        return True
    except:
        return False
### --- Función para buscar usuario en la base de datos --- ###
@sync_to_async
def buscar_en_base_de_datos(phone_number):
    try:
        return UserAdmin.objects.get(phone=phone_number)
    except ObjectDoesNotExist:
        return None  # Retorna None en lugar de False para evitar errores

### --- Función para registrar el Admin --- ###
@sync_to_async
def registrar_admin(phone_number, telegram_id):
    try:
        admin = UserAdmin.objects.get(phone=phone_number)
        admin.telegram_id = telegram_id
        admin.save()
        return True
    except ObjectDoesNotExist:
        return False

### --- Configuración del bot --- ###
def main():
    token = config("TOKEN_TELEGRAMADMIN")
    app = ApplicationBuilder().token(token).build()

    # Comandos y manejadores
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))  # Manejador para recibir contactos
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))  # Mensajes de texto normales
    app.add_handler(CallbackQueryHandler(button))  # Manejar respuestas de botones

    # Iniciar el bot
    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()