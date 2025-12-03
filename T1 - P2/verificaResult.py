import os

def validar():
    print("="*40 + "\nVALIDACAO DO SISTEMA\n" + "="*40)
    
    # [cite_start]1. Valida Log (GRANT -> RELEASE) [cite: 39]
    try:
        with open('log_coordenador.txt', 'r') as f: lines = f.readlines()
        print(f"Log: {len(lines)} eventos.")
        ativo, erros = None, 0
        
        for l in lines:
            parts = l.strip().split('|')
            if len(parts) < 3: continue
            tipo, pid, direcao = parts[1], parts[2], parts[3]
            
            if tipo == 'GRANT' and direcao == 'ENVIADA':
                if ativo: 
                    print(f"[ERRO] GRANT para {pid} enquanto {ativo} ativo.")
                    erros += 1
                ativo = pid
            elif tipo == 'RELEASE' and direcao == 'RECEBIDA':
                if ativo != pid:
                    print(f"[ERRO] RELEASE de {pid} mas {ativo} era ativo.")
                    erros += 1
                ativo = None
        
        if erros == 0: print("[OK] Sequencia GRANT -> RELEASE correta.")
        else: print(f"[FALHA] {erros} erros de logica no log.")
    except Exception as e: print(f"Erro no log: {e}")

    # [cite_start]2. Valida Resultado.txt (Linhas e Consistencia) [cite: 36, 37]
    try:
        if not os.path.exists('resultado.txt'):
            print("[ERRO] resultado.txt nao existe.")
            return

        with open('resultado.txt', 'r') as f: lines = f.readlines()
        print(f"Resultado: {len(lines)} escritas.")
        
        contagem = {}
        for l in lines:
            pid = l.split('|')[0].strip().split()[-1]
            contagem[pid] = contagem.get(pid, 0) + 1
            
        print("Escritas por Processo:")
        for pid, qtd in sorted(contagem.items()):
            print(f"  Proc {pid}: {qtd}")
            
    except Exception as e: print(f"Erro ao ler resultado: {e}")

if __name__ == "__main__":
    validar()