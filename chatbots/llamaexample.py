import torch
from transformers import pipeline

import time
from datetime import datetime

model_id = "meta-llama/Llama-3.2-3B-Instruct"
pipe = pipeline(
    "text-generation",
    model=model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
start = time.time()
print("Llega mensaje")
messages = [
    {"role": "system", "content": "You are a pirate chatbot who always responds in spanish pirate speak!"},
    {"role": "user", "content": "Quien eres?"},
]
outputs = pipe(
    messages,
    max_new_tokens=256,
)
print(outputs[0]["generated_text"][-1])
end = time.time()
print(f"Tiempo de ejecución: {end - start} segundos")
