import subprocess, time, sys, os

def run(n_procs):
    # Limpa arquivos anteriores
    for f in ['resultado.txt', 'log_coordenador.txt']:
        if os.path.exists(f): os.remove(f)

    print(f"Iniciando Coordenador e {n_procs} processos...")
    coord = subprocess.Popen([sys.executable, 'coordenador.py'])
    time.sleep(2)
    
    # Inicia processos sequencialmente
    procs = []
    for i in range(1, n_procs + 1):
        procs.append(subprocess.Popen([sys.executable, 'processo.py', str(i)]))
    
    for p in procs: p.wait()
    
    # NOVO: Pequeno atraso para garantir que os logs e dados finais sejam gravados.
    time.sleep(1) 
    
    print("Processos finalizados. Encerrando coordenador...")
    coord.terminate()
    coord.wait()
    print("Teste finalizado. Execute 'python verificar_resultado.py' para validar.")

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit("Uso: python executar_teste.py <n_processos>")
    run(int(sys.argv[1]))