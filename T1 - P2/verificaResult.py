import os

def verificar_garantia_grant_release():
    """
    Verifica se APÓS CADA GRANT há um RELEASE
    """
    print("="*70)
    print("VERIFICAÇÃO: APÓS CADA GRANT HÁ UM RELEASE")
    print("="*70)
    
    if not os.path.exists('log_coordenador.txt'):
        print("ERRO: log_coordenador.txt não encontrado")
        return
    
    with open('log_coordenador.txt', 'r') as f:
        eventos = [linha.strip() for linha in f if linha.strip()]
    
    print(f"Total de eventos: {len(eventos)}")
    print("\nANÁLISE DA SEQUÊNCIA:")
    print("-"*70)
    
    # Buscar padrões GRANT -> (qualquer coisa) -> RELEASE
    grants_por_processo = {}
    problemas = []
    i = 0
    
    while i < len(eventos):
        partes = eventos[i].split(' | ')
        if len(partes) >= 4:
            timestamp, tipo, processo_str, direcao = partes[0], partes[1], partes[2], partes[3]
            
            if tipo == 'GRANT' and direcao == 'ENVIADA':
                print(f"\n✓ ENCONTRADO GRANT para Processo {processo_str}")
                print(f"  {eventos[i]}")
                
                # Registrar este GRANT
                grants_por_processo[processo_str] = grants_por_processo.get(processo_str, 0) + 1
                
                # Procurar RELEASE correspondente
                encontrou_release = False
                j = i + 1
                
                while j < len(eventos):
                    partes2 = eventos[j].split(' | ')
                    if len(partes2) >= 4:
                        tipo2, processo_str2, direcao2 = partes2[1], partes2[2], partes2[3]
                        
                        # Verificar se encontrou outro GRANT antes do RELEASE
                        if tipo2 == 'GRANT' and direcao2 == 'ENVIADA':
                            print(f"  ✗ PROBLEMA: Outro GRANT antes do RELEASE!")
                            print(f"    {eventos[j]}")
                            problemas.append(f"GRANT para {processo_str2} antes do RELEASE de {processo_str}")
                            break
                        
                        # Verificar se encontrou o RELEASE correto
                        if tipo2 == 'RELEASE' and direcao2 == 'RECEBIDA' and processo_str2 == processo_str:
                            print(f"  ✓ ENCONTRADO RELEASE correspondente")
                            print(f"    {eventos[j]}")
                            encontrou_release = True
                            i = j  # Avançar até o RELEASE
                            break
                    
                    j += 1
                
                if not encontrou_release:
                    print(f"  ✗ PROBLEMA: GRANT sem RELEASE correspondente!")
                    problemas.append(f"GRANT para {processo_str} sem RELEASE")
        
        i += 1
    
    # Resumo
    print("\n" + "="*70)
    print("RESUMO DA VERIFICAÇÃO")
    print("="*70)
    
    if problemas:
        print(f"PROBLEMAS ENCONTRADOS ({len(problemas)}):")
        for p in problemas:
            print(f"  • {p}")
        print(f"\n✗ O sistema NÃO garante que após cada GRANT há um RELEASE")
    else:
        print("✓ TODOS OS GRANTS TÊM RELEASE CORRESPONDENTE")
        print("✓ O sistema GARANTE que após cada GRANT há um RELEASE")
        print("✓ Requisito do trabalho SATISFEITO")
    
    # Estatísticas
    print(f"\nESTATÍSTICAS:")
    for processo in sorted(grants_por_processo.keys()):
        print(f"  Processo {processo}: {grants_por_processo[processo]} GRANT(s)")

if __name__ == "__main__":
    verificar_garantia_grant_release()