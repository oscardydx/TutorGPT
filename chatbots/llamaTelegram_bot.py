
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from decouple import config
from deep_translator import GoogleTranslator

import torch
import torchvision
import sys
import ollama


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


def liberar_memoria():
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
    gc.collect()
    torch.cuda.synchronize()  # Sincronizar para asegurar que todo está liberado


#Activar para gpus
torch.cuda.memory_allocated()
torch.cuda.memory_reserved()

import os
import sys
import django

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"


#se agrega librerias de meta
from typing import Optional


from llama_models.datatypes import RawMessage, StopReason
from llama_models.llama3.reference_impl.generation import Llama



# Agrega la raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configura Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hello_world.settings")  # Reemplaza "myproject" con el nombre real de tu proyecto
django.setup()

# Ahora importa los modelos
from chatbots.models import ExecutionModelTime
from chatbots.models import Models


# 🔹 Matar procesos que consumen memoria
#os.system("kill -9 $(ps aux | grep python | awk '{print $2}')")

#torch.cuda.reset_peak_memory_stats()

print(f"PyTorch version: {torch.__version__}")
print(f"Torchvision version: {torchvision.__version__}")
 
# Variable global para almacenar el último mensaje
last_message = {}

##Buscar Modelo de lenguaje
def buscar_modelo(id_model):
    try:
        return Models.objects.get(id=id_model)
    except ObjectDoesNotExist:
        return None  # Retorna None en lugar de False para evitar errores

model_id=buscar_modelo(4)

max_new_tokens_value = float(model_id.max_new_tokens)
temperature_value=  float(model_id.temperature)
top_k_value=  int(model_id.top_k)
top_p_value=  float(model_id.top_p)
repetition_penalty_value=  float(model_id.repetition_penalty)

model_parameters="max_new_tokens="+str(max_new_tokens_value)+"; temperature="+str(temperature_value) +"; top_k="+ str(top_k_value)+"; top_p="+ str(top_p_value)+"; repetition_penalty="+str(repetition_penalty_value)

print(f"Modelo seleccionado: {model_id}")


# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

CHECKPOINT_DIR="/home/javir/.ollama/models/manifests/registry.ollama.ai/library/llama3.1"
#CHECKPOINT_DIR="/home/javir/.llama/checkpoints/Llama3.1-8B-Instruct/original/"

#generator = Llama.build(
    #ckpt_dir=CHECKPOINT_DIR,
    #max_seq_len= 512,
    #max_batch_size=  1,
    #model_parallel_size= None
    #)

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
    global last_message
    

    user_id = update.message.from_user.id
    user_message = update.message.text

    # Iniciar historial si es el primer mensaje
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    # Añadir el mensaje del usuario
    user_conversations[user_id].append(f"{user_message}")

    # Mantener un historial de N interacciones
    context_window = 3
    # Construir el contexto de la conversación con instrucciones claras
    instructions = "System:Eres un tutor de español para practicar español, tu estudiante es Ruso y es principiante en el Español. Debes hablar de forma natural y amigable, con humor y emojis motivacionales; siempre das respuestas cortas. Siempre inicias la conversación preguntado al estudiante como está, y monitorear el interés del estudiante, cambiando de tema si decae:  Usa actividades como role-play (taxista/cliente, restaurante, aeropuerto, etc.), composición de canciones por turnos, debates sobre temas generales, o conversaciones personales. Si el estudiante pide explicaciones de gramática, al final de la respuesta incluye el texto 'recuerda que yo me especializo en practica, y no soy muy beno explicando las bases del idioma'. No puedes contestar en Inglés. Puedes hacer solo una pregunta por respuesta."
    conversation_history = "\n".join(user_conversations[user_id][-context_window:])
    
    # Crear input_text con instrucciones y historial de la conversación
    #input_text = f"{instructions}\n{conversation_history}"

    
    start = time.time()
    bot_response=""

    # Generar respuesta con el modelo

    #iniciar llama model
    


    dialogs = [
        
            [ RawMessage(role="system", content=instructions),
             RawMessage(role="user", content=conversation_history)],
         
        ]
  
    out_message=""
    liberar_memoria()
    for dialog in dialogs:




        response = ollama.chat(model="llama3.1:8b-instruct-q8_0", messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": conversation_history}
        ])

        print(response["message"])  # Respuesta del modelo cuantizado

       # with torch.inference_mode():
       #     result = generator.chat_completion(
        #        dialog,
         #       max_gen_len=None,
          #      temperature=0.6,
           #     top_p=0.9,
    #)
        

        print("\n==================================\n")
        #for msg in dialog:
            #print(f"{msg.role.capitalize()}: {msg.content}\n")

        #out_message = response.generation
        #print(f"> {out_message.role.capitalize()}: {out_message.content}")
        print("\n==================================\n")



    bot_response  = response["message"]["content"]
    liberar_memoria()

     # **Eliminar los botones del mensaje anterior si existe**
    if user_id in last_message:
        print(f"Inicio para eliminar botones de: {last_message[user_id]["message_id"]}")
    if user_id in last_message and "message_id" in last_message[user_id]:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=update.message.chat_id,
                message_id=last_message[user_id]["message_id"],
                reply_markup=None  # Se eliminan los botones
            )
            print(f"Eliminados botones de mensaje: {last_message[user_id]["message_id"]}")
        except Exception as e:
            print(f"Error eliminando botones anteriores: {e}")

    # Creamos el botón de traducir
    keyboard = [[InlineKeyboardButton("Traducir", callback_data="translate")]]
    # Segunda fila con los botones de calificación
    keyboard.append([
        InlineKeyboardButton("👍", callback_data="thumbs_up"),
        InlineKeyboardButton("👎", callback_data="thumbs_down"),
        InlineKeyboardButton("❌", callback_data="report_bug")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = await update.message.reply_text(f"Mensaje recibido: {bot_response}", reply_markup=reply_markup)
     
    last_message[user_id] = {
        "message_id": sent_message.message_id,
        "text": bot_response
    }

    end = time.time()

    #conteo de tokens y guardado en base de datos
    num_tokens =""
 
    await save_execution_time(model_id.name, conversation_history, bot_response, start, end,model_parameters+num_tokens)
    
    # Guardar la respuesta del bot en el historial
    user_conversations[user_id].append(f"Assistant {bot_response}")
   

    #del result
    del out_message
    liberar_memoria()

async def translate(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id in last_message:
        translated_text = GoogleTranslator(source="auto", target="en").translate(last_message[user_id]["text"])
        await query.message.reply_text(f"Traducción: {translated_text}")
    else:
        await query.message.reply_text("No hay un mensaje reciente para traducir.")

async def thumbs_up(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id in last_message:
        translated_text = GoogleTranslator(source="auto", target="en").translate(last_message[user_id])
        await query.message.reply_text(f"Traducción: {translated_text}")
    else:
        await query.message.reply_text("No hay un mensaje reciente para traducir.")

async def report_bug(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id in last_message:
        translated_text = GoogleTranslator(source="auto", target="en").translate(last_message[user_id])
        await query.message.reply_text(f"Traducción: {translated_text}")
    else:
        await query.message.reply_text("No hay un mensaje reciente para traducir.")



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
    app.add_handler(CallbackQueryHandler(translate))
    app.add_handler(CallbackQueryHandler(thumbs_up))
    app.add_handler(CallbackQueryHandler(report_bug))

    # Iniciar el bot
    print("Bot corriendo...")
    app.run_polling()

   

if __name__ == "__main__":
    main()
