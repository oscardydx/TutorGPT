import os
import sys
import django
import torch

torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()
#Activar para gpus
torch.cuda.memory_allocated()
torch.cuda.memory_reserved()
# 🔹 Matar procesos que consumen memoria
#os.system("kill -9 $(ps aux | grep python | awk '{print $2}')")

os.system("kill -9 $(ps aux | grep '[t]elegram_bot.py' | awk '{print $2}')")

