import subprocess
import time
import sys

def testar_sistema(num_processos):
    """Testa o sistema com múltiplos processos"""
    
    print("="*60)
    print(f"TESTE DO SISTEMA DE EXCLUSÃO MÚTUA")
    print(f"Processos: {num_processos}")
    print("="*60)
    
    # Limpar arquivos anteriores
    try:
        import os
        if os.path.exists('resultado.txt'):
            os.remove('resultado.txt')
        if os.path.exists('log_coordenador.txt'):
            os.remove('log_coordenador.txt')
    except:
        pass
    
    # Passo 1: Iniciar coordenador
    print("\n[1/3] Iniciando coordenador...")
    coordenador = subprocess.Popen(
        [sys.executable, 'coordenador.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Dar tempo para o coordenador iniciar
    time.sleep(3)
    
    # Verificar se coordenador está rodando
    if coordenador.poll() is not None:
        print("ERRO: Coordenador não iniciou")
        return
    
    print("Coordenador iniciado com sucesso")
    
    # Passo 2: Iniciar processos
    print(f"\n[2/3] Iniciando {num_processos} processos...")
    processos = []
    
    for i in range(1, num_processos + 1):
        print(f"  Iniciando Processo {i}...")
        p = subprocess.Popen(
            [sys.executable, 'processo.py', str(i)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processos.append(p)
        time.sleep(0.5)  # Pequeno delay entre processos
    
    # Passo 3: Aguardar processos terminarem
    print("\n[3/3] Aguardando processos terminarem...")
    
    for i, p in enumerate(processos, 1):
        p.wait()
        print(f"  Processo {i} finalizado")
    
    # Passo 4: Finalizar coordenador
    print("\nFinalizando coordenador...")
    coordenador.terminate()
    coordenador.wait()
    
    # Passo 5: Mostrar resultados
    print("\n" + "="*60)
    print("RESULTADOS")
    print("="*60)
    
    try:
        # Ler arquivo de resultado
        with open('resultado.txt', 'r') as f:
            linhas = f.readlines()
        
        print(f"Entradas em resultado.txt: {len(linhas)}")
        
        # Contar por processo
        contagem = {}
        for linha in linhas:
            if 'Processo' in linha:
                partes = linha.split('|')
                if len(partes) > 0:
                    pid = partes[0].strip().split()[-1]
                    contagem[pid] = contagem.get(pid, 0) + 1
        
        print("\nAcessos por processo:")
        for pid in sorted(contagem.keys()):
            print(f"  Processo {pid}: {contagem[pid]} acesso(s)")
        
        # Verificar log
        with open('log_coordenador.txt', 'r') as f:
            logs = f.readlines()
        
        print(f"\nEventos no log: {len(logs)}")
        
        # Verificar sequência GRANT->RELEASE
        print("\nVerificando sequência GRANT->RELEASE...")
        
        processo_ativo = None
        problemas = 0
        
        for i, log in enumerate(logs):
            partes = log.split('|')
            if len(partes) >= 4:
                partes = [p.strip() for p in partes]
                tipo = partes[1]
                processo = partes[2]
                direcao = partes[3]
                
                if tipo == 'GRANT' and direcao == 'ENVIADA':
                    if processo_ativo is not None:
                        print(f"  ERRO linha {i+1}: GRANT para Processo {processo} enquanto Processo {processo_ativo} ativo")
                        problemas += 1
                    processo_ativo = processo
                
                elif tipo == 'RELEASE' and direcao == 'RECEBIDA':
                    if processo_ativo != processo:
                        print(f"  ERRO linha {i+1}: RELEASE do Processo {processo} mas Processo {processo_ativo} ativo")
                        problemas += 1
                    processo_ativo = None
        
        if problemas == 0:
            print("  ✓ Sequência GRANT->RELEASE correta!")
        else:
            print(f"  ✗ {problemas} problema(s) encontrado(s)")
    
    except FileNotFoundError as e:
        print(f"Arquivo não encontrado: {e}")
    except Exception as e:
        print(f"Erro ao ler resultados: {e}")
    
    print("\nTeste completo!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python executar_teste.py <num_processos>")
        print("Exemplo: python executar_teste.py 3")
        sys.exit(1)
    
    try:
        num = int(sys.argv[1])
        if num < 1:
            print("Número de processos deve ser pelo menos 1")
            sys.exit(1)
        
        testar_sistema(num)
    except ValueError:
        print("Número de processos deve ser um inteiro")
        sys.exit(1)