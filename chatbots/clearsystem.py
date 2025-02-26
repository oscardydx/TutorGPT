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
os.system("kill -9 $(ps aux | grep python  | awk '{print $2}')")

#os.system("kill -9 $(ps aux | grep '[t]elegram_bot.py' | awk '{print $2}')")



#gpu_process_id = 3426828  # Reemplaza con el ID de tu proceso
#os.system(f"kill -9 {gpu_process_id}")

import os
import signal
import subprocess

def get_python_processes():
    """ Obtiene la lista de procesos Python en ejecución con sus PIDs. """
    try:
        result = subprocess.run(["pgrep", "-f", "python"], capture_output=True, text=True)
        pids = result.stdout.strip().split("\n")  # Obtener lista de PIDs
        return [int(pid) for pid in pids if pid.isdigit()]
    except Exception as e:
        print(f"Error al obtener procesos Python: {e}")
        return []

def kill_process(pid):
    """ Mata un proceso dado su PID. """
    try:
        os.kill(pid, signal.SIGKILL)
        print(f"✅ Proceso {pid} eliminado.")
    except ProcessLookupError:
        print(f"⚠ Proceso {pid} no encontrado.")
    except Exception as e:
        print(f"❌ Error al eliminar proceso {pid}: {e}")

def clear_gpu():
    """ Libera memoria de la GPU si PyTorch está instalado. """
    try:
        import torch
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        print("✅ Memoria de la GPU liberada.")
    except ImportError:
        print("⚠ PyTorch no está instalado, no se puede liberar la GPU.")

if __name__ == "__main__":
    python_pids = get_python_processes()
    
    if python_pids:
        print(f"🔍 Procesos Python encontrados: {python_pids}")
        for pid in python_pids:
            kill_process(pid)
    else:
        print("✅ No hay procesos Python en ejecución.")
    
    clear_gpu()

