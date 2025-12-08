import os

def validar():
    print("="*40 + "\nVALIDACAO DO SISTEMA\n" + "="*40)
    
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
            if len(parts) < 4: continue
            timestamp, tipo, pid, direcao = parts[0], parts[1], parts[2], parts[3]
            
            # --- VERIFICAÇÃO DE INTERCALAÇÃO ---
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
        
        if erros == 0: print("[OK] Sequencia GRANT -> RELEASE esta logicamente correta (Exclusao Mutua respeitada).")
        else: print(f"[FALHA] {erros} erros de logica no log.")
    except Exception as e: print(f"[FALHA] Erro ao analisar log: {e}")

    print("-"*40)

    # 2. Valida Resultado.txt (n*r linhas e contagem por processo)
    try:
        if not os.path.exists('resultado.txt'):
            print("[FALHA] resultado.txt nao existe. Nenhuma escrita na RC ocorreu.")
            return

        with open('resultado.txt', 'r') as f: lines = f.readlines()
        
        contagem = {}
        for l in lines:
            try:
                pid = l.split('|')[0].strip().split()[-1]
                contagem[pid] = contagem.get(pid, 0) + 1
            except IndexError:
                pass
            
        n_total = len(contagem)
        r_esperado = 3 
        total_obtido = len(lines)

        print(f"Total de Processos distintos detectados: {n_total}")
        print(f"Total de escritas obtidas: {total_obtido}")

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
    validar()