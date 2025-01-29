import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from decouple import config
from transformers import pipeline
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

import torchvision

print(f"PyTorch version: {torch.__version__}")
print(f"Torchvision version: {torchvision.__version__}")

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

#model_id = "meta-llama/Llama-3.2-3B-Instruct"
model_id ="Qwen/Qwen2.5-7B-Instruct"
#model_id ="gpt2"

# Cargar el tokenizador y modelo
tokenizer = AutoTokenizer.from_pretrained(model_id,padding_side="left")
model = AutoModelForCausalLM.from_pretrained(model_id, device_map=None, offload_folder="offload_dir", torch_dtype=torch.float16).to(device)

# Asignar manualmente el pad_token_id si es necesario
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Crear el pipeline usando el modelo y tokenizador cargados
generator = pipeline("text-generation", model=model,  tokenizer=tokenizer,device=0 )


# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Mantener un historial de la conversación para usar en las respuestas
user_conversations = {}

# Función para manejar mensajes de texto
async def start(update: Update, context):
    # Crear un botón que permita al usuario enviar su número
    contact_button = KeyboardButton("Enviar mi número de teléfono", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True)

    # Enviar mensaje con el botón
    await update.message.reply_text("¡Hola! Soy tu bot de Telegram. Por favor, comparte tu número de teléfono.", reply_markup=reply_markup)

async def echo(update: Update, context):

    print("Llego mensaje.....")
    user_id = update.message.from_user.id
    user_message = update.message.text

    # Iniciar una nueva conversación si es el primer mensaje
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    # Añadir el mensaje del usuario al historial de conversación
    user_conversations[user_id].append(f"Usuario: {user_message}")

    # Solo utilizar el último mensaje para generar la respuesta
    input_text = user_conversations[user_id][-1]

    # Generar una respuesta con el modelo DialoGPT
    conversation = generator(input_text, max_length=100, truncation=True)

    # Imprimir la respuesta para depuración
    print(conversation)  # Aquí vemos cómo está estructurada la respuesta

    # Acceder a la respuesta generada
    bot_response = conversation[0]['generated_text']

    # Añadir la respuesta del bot al historial de conversación
    user_conversations[user_id].append(f"Bot: {bot_response}")

    # Enviar la respuesta al usuario
    await update.message.reply_text(f" {bot_response}")

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