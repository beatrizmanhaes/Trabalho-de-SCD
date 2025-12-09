import subprocess, time, sys, os

def run(n_procs, r_reps):
    # Limpa arquivos anteriores
    for f in ['resultado.txt', 'log_coordenador.txt']:
        if os.path.exists(f): os.remove(f)

    print(f"Iniciando Coordenador e {n_procs} processos com r={r_reps} repetições...")
    coord = subprocess.Popen([sys.executable, 'coordenador.py'])
    time.sleep(2) # Tempo para coord iniciar
    
    # Inicia processos
    procs = []
    
    for i in range(1, n_procs + 1):
        procs.append(subprocess.Popen([sys.executable, 'processo.py', str(i), str(r_reps)]))
    
    # Aguarda a conclusão de todos os processos
    for p in procs: p.wait()
    
    time.sleep(1) # Garante que o último RELEASE seja logado
    
    print("Processos finalizados. Encerrando coordenador...")
    coord.terminate()
    coord.wait()
    # Instrução atualizada para o script de validação
    print(f"Teste finalizado. Execute 'python verificar_resultado.py {r_reps}' para validar.")

if __name__ == "__main__":
    if len(sys.argv) != 3: 
        sys.exit("Uso: python executar_teste.py <n_processos> <r_repeticoes>")
    try:
        n = int(sys.argv[1])
        r = int(sys.argv[2])
        run(n, r)
    except ValueError:
        sys.exit("Ambos os argumentos devem ser números inteiros.")