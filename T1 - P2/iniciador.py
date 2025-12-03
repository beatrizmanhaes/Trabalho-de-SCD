import subprocess
import time
import sys

def iniciar_processos(num_processos):
    # Iniciar coordenador em background
    print("Iniciando coordenador...")
    coordenador_process = subprocess.Popen([sys.executable, 'coordenador.py'])
    
    # Aguardar coordenador iniciar
    time.sleep(2)
    
    # Iniciar processos sequencialmente
    processos = []
    for i in range(1, num_processos + 1):
        print(f"Iniciando processo {i}...")
        process = subprocess.Popen([sys.executable, 'processo.py', str(i)])
        processos.append(process)
        time.sleep(0.5)  # Pequeno delay entre processos
    
    # Aguardar todos os processos terminarem
    for process in processos:
        process.wait()
    
    print("Todos os processos finalizados")
    coordenador_process.terminate()

if __name__ == "__main__":
    num_processos = 3  # Alterar conforme necessário
    iniciar_processos(num_processos)