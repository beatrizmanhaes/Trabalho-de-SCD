import subprocess, time, sys, os

def run(n_procs):
    # Limpa arquivos anteriores
    for f in ['resultado.txt', 'log_coordenador.txt']:
        if os.path.exists(f): os.remove(f)

    print(f"Iniciando Coordenador e {n_procs} processos...")
    coord = subprocess.Popen([sys.executable, 'coordenador.py'])
    time.sleep(2) # Tempo para coord iniciar
    
    # Inicia processos
    procs = []
    for i in range(1, n_procs + 1):
        procs.append(subprocess.Popen([sys.executable, 'processo.py', str(i)]))
    
    # Aguarda a conclusão de todos os processos
    for p in procs: p.wait()
    
    time.sleep(1) # Garante que o último RELEASE seja logado
    
    print("Processos finalizados. Encerrando coordenador...")
    coord.terminate()
    coord.wait()
    print("Teste finalizado. Execute 'python verificar_resultado.py' para validar.")

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit("Uso: python executar_teste.py <n_processos>")
    try:
        run(int(sys.argv[1]))
    except ValueError:
        sys.exit("O argumento deve ser um número inteiro.")