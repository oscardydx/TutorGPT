import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from decouple import config
from transformers import pipeline

# Crear un pipeline para generación de texto
generator = pipeline("text-generation", model="EleutherAI/gpt-neo-1.3B")



# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Función para manejar mensajes de texto
async def start(update: Update, context):
    # Crear un botón que permita al usuario enviar su número
    contact_button = KeyboardButton("Enviar mi número de teléfono", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True)

    # Enviar mensaje con el botón
    await update.message.reply_text("¡Hola! Soy tu bot de Telegram. Por favor, comparte tu número de teléfono.", reply_markup=reply_markup)

async def echo(update: Update, context):
    # Prueba básica con truncation activado
    output = generator(update.message.text, max_length=50, num_return_sequences=1, truncation=True)

    await update.message.reply_text(f"Respuesta GPT: {output[0]['generated_text']}")

# Función para manejar el número de teléfono enviado
async def handle_contact(update: Update, context):
    # Verificar si el mensaje contiene un contacto
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        user_id = update.message.from_user.id

        # Aquí iría la lógica para consultar la base de datos
        # Si el número de teléfono está en la base de datos, responder si es cliente o no

        # Simulamos la búsqueda en la base de datos
        es_cliente = buscar_en_base_de_datos(phone_number)

        if es_cliente:
            await update.message.reply_text(f"El número {phone_number} es un cliente.")
        else:
            await update.message.reply_text(f"El número {phone_number} NO es un cliente.")
    else:
        await update.message.reply_text("No se ha recibido un número de teléfono válido.")

# Función para simular la búsqueda en la base de datos
def buscar_en_base_de_datos(phone_number):
    # Lógica para buscar el número en la base de datos (ejemplo con una lista simulada)
    clientes = ['123456789', '987654321', '555555555']
    return phone_number in clientes

# Configuración del bot
def main():
    token = config("TOKEN_TELEGRAM")
    app = ApplicationBuilder().token(token).build()

    # Comandos y manejadores
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))  # Añadir el handler para el contacto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Iniciar el bot
    print("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
