import os, sys

def validar(r_esperado):
    # Garante que r_esperado é um inteiro
    try:
        r_esperado = int(r_esperado)
    except ValueError:
        print("[ERRO FATAL] O número de repetições esperado deve ser um número inteiro.")
        return
        
     
    # 1. Valida Log (GRANT -> RELEASE intercalado)
    try:
        if not os.path.exists('log_coordenador.txt'):
            print("[FALHA] log_coordenador.txt nao encontrado.")
            return

        with open('log_coordenador.txt', 'r') as f: lines = f.readlines()
        print(f"Log: {len(lines)} eventos registrados.")
        ativo, erros = None, 0
        
        # Itera sobre o log para verificar a alternância estrita
        for l in lines:
            parts = l.strip().split('|')
            if len(parts) != 4: return
            timestamp, tipo, pid, direcao = parts[0], parts[1], parts[2], parts[3]
            
            # --- VERIFICAÇÃO DE INTERCALAÇÃO --- Um GRANT só pode ocorrer caso um RELEASE tiver ocorrido
            if tipo == 'GRANT' and direcao == 'ENVIADA':
                if ativo: 
                    print(f"[ERRO] {timestamp}: GRANT para {pid} ENVIADA, mas RC ja estava ocupada por {ativo}. FALHA NA EXCLUSAO MÚTUA!")
                    erros += 1
                ativo = pid
            elif tipo == 'RELEASE' and direcao == 'RECEBIDA':
                if ativo != pid:
                    print(f"[ERRO] {timestamp}: RELEASE de {pid} RECEBIDA, mas o processo ativo era {ativo}. FALHA NA INTERCALAÇÃO!")
                    erros += 1
                else:
                    ativo = None # RC LIBERADA, espera o próximo GRANT
        
        if erros != 0: print(f"[FALHA] {erros} erros de logica no log.")
    except Exception as e: print(f"[FALHA] Erro ao analisar log: {e}")


    # 2. Valida Resultado.txt (n*r linhas e contagem por processo)
    try:
        if not os.path.exists('resultado.txt'):
            print("[FALHA] resultado.txt nao existe. Nenhuma escrita na RC ocorreu.")
            return

        with open('resultado.txt', 'r') as f: lines = f.readlines()
        
        contagem = {} # Chave - PID , Valor - Qtd r
        for l in lines:
            try:
                pid = l.split('|')[0].strip().split()[-1] # Formatação linhas de resultado.txt
                contagem[pid] = contagem.get(pid, 0) + 1 # get para evitar o KeyError
            except IndexError:
                pass
            
        n_total = len(contagem)
        total_obtido = len(lines)

        print(f"Total de Processos distintos detectados: {n_total}")
        print(f"Total de escritas obtidas: {total_obtido}")
        print(f"Repetições (r) esperadas por processo: {r_esperado}")

        erros_p = 0
        print("\nEscritas por Processo:")
        for pid, qtd in sorted(contagem.items()):
            if qtd != r_esperado:
                print(f"  [ERRO] Proc {pid}: {qtd} (Esperado: {r_esperado})")
                erros_p += 1
            else:
                print(f"  [OK] Proc {pid}: {qtd}")
                
        if erros_p > 0:
             print(f"[FALHA] {erros_p} processo(s) nao executaram o numero correto de repetições (r).")
        
    except Exception as e: 
        print(f"[FALHA] Erro ao ler resultado.txt: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2: 
        sys.exit("Uso: python verificar_resultado.py <r_repeticoes_esperadas>")
    
    # Pega o valor de r (repetições) do argumento de linha de comando
    validar(sys.argv[1])