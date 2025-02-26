import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from decouple import config
from transformers import pipeline
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import torchvision
import sys


from django.core.exceptions import ObjectDoesNotExist

print(f"version python {sys.version}")

from huggingface_hub import login
# Iniciar sesión en Hugging Face con tu token
login(config("HUGGENSFACESECRET"))

import time
from datetime import datetime
from django.db import transaction
from django.db.models import Model
from asgiref.sync import sync_to_async



import gc

# 🔹 Liberar RAM antes de cargar el modelo
gc.collect()
torch.cuda.empty_cache()

#Activar para gpus
##torch.cuda.memory_allocated()
##torch.cuda.memory_reserved()

import os
import sys
import django

# Agrega la raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configura Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hello_world.settings")  # Reemplaza "myproject" con el nombre real de tu proyecto
django.setup()

# Ahora importa los modelos
from chatbots.models import ExecutionModelTime
from chatbots.models import Models

#importar modelo yandex desde la API 
import requests
def yandex_gpt_request(prompt, temperature, max_tokens):
    headers = {
        "Authorization": f"Bearer {config("IAM_TOKEN")}",
        "Content-Type": "application/json"
    }
    
    data = {
        "modelUri": f"gpt://{config("FOLDER_ID")}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": max_tokens
        },
        "messages": [{"role": "user", "text": prompt}]
    }

    response = requests.post(config("ENDPOINT"), json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
    else:
        return f"Error {response.status_code}: {response.text}"

# 🔹 Matar procesos que consumen memoria
#os.system("kill -9 $(ps aux | grep python | awk '{print $2}')")

#torch.cuda.reset_peak_memory_stats()

print(f"PyTorch version: {torch.__version__}")
print(f"Torchvision version: {torchvision.__version__}")

#device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

##Buscar Modelo de lenguaje
def buscar_modelo(id_model):
    try:
        return Models.objects.get(id=id_model)
    except ObjectDoesNotExist:
        return None  # Retorna None en lugar de False para evitar errores

model_id=buscar_modelo(2)

max_new_tokens_value = float(model_id.max_new_tokens)
temperature_value=  float(model_id.temperature)
top_k_value=  int(model_id.top_k)
top_p_value=  float(model_id.top_p)
repetition_penalty_value=  float(model_id.repetition_penalty)

model_parameters="max_new_tokens="+str(max_new_tokens_value)+"; temperature="+str(temperature_value) +"; top_k="+ str(top_k_value)+"; top_p="+ str(top_p_value)+"; repetition_penalty="+str(repetition_penalty_value)

print(f"Modelo seleccionado: {model_id}")



# Cargar el tokenizador y modelo
if(model_id.API==False):
    tokenizer = AutoTokenizer.from_pretrained(model_id,padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", offload_folder="offload_dir", torch_dtype=torch.bfloat16,trust_remote_code=True)


    # Asignar manualmente el pad_token_id si es necesario
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Crear el pipeline usando el modelo y tokenizador cargados
    generator = pipeline("text-generation", model=model,  tokenizer=tokenizer,trust_remote_code=True )
    #generator = pipeline("text-generation", model=model,  tokenizer=tokenizer,device=0,trust_remote_code=True )


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

    # Iniciar historial si es el primer mensaje
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    # Añadir el mensaje del usuario
    user_conversations[user_id].append(f"Usuario: {user_message}")

    # Mantener un historial de N interacciones
    context_window = 2
    # Construir el contexto de la conversación con instrucciones claras
    instructions = """Responde de manera clara y concisa. 
No generes preguntas adicionales o notas a menos que el usuario lo solicite. 
Si el usuario dice "gracias", responde solo con "¡De nada! 😊".
"""
    conversation_history = "\n".join(user_conversations[user_id][-context_window:])
    
    # Crear input_text con instrucciones y historial de la conversación
    input_text = f"{instructions}\n{conversation_history}"

    #se agrega codigo para mejorar deepseek

    # Formato con roles
    #input_text = f"""
    #[system]
    #{instructions}

    #[user]
    #{conversation_history}

    #[assistant]
    #"""

  
    
    start = time.time()
    bot_response=""
    if(model_id.API):
        bot_response = yandex_gpt_request(input_text,temperature_value,int(max_new_tokens_value))
    else:
        # Generar respuesta con el modelo
        conversation = generator(input_text, max_new_tokens=max_new_tokens_value,  
                                temperature=temperature_value, truncation=True,
                                top_k=top_k_value, top_p=top_p_value, 
                                repetition_penalty=repetition_penalty_value,
                                return_full_text=False, do_sample=True)

        bot_response = conversation[0]['generated_text'].replace(input_text, "").strip()

   
    
    end = time.time()

    #conteo de tokens y guardado en base de datos
    num_tokens =""
    if(model_id.API==False):
        num_tokens = "; tokens_input="+str(len(tokenizer.encode(input_text, add_special_tokens=True)))+"; tokens_output="+str(len(tokenizer.encode(bot_response, add_special_tokens=True)))
    await save_execution_time(model_id.name, conversation_history, bot_response, start, end,model_parameters+num_tokens)
    
    # Guardar la respuesta del bot en el historial
    user_conversations[user_id].append(f"Bot: {bot_response}")
    # Enviar respuesta al usuario
    await update.message.reply_text(f"{bot_response}")



@sync_to_async
def save_execution_time(model_id, input_text, bot_response, start, end,parameters):

    execution = ExecutionModelTime.objects.create(model_name=model_id)
    execution.pregunta = input_text
    execution.respuesta = bot_response
    execution.time = end - start
    execution.parameters = parameters
    
    execution.save()
    print(execution.date)
    print(f"Tiempo de ejecución: {end - start} segundos")

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