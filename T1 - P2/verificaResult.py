import os
from collections import defaultdict

def verificar_resultado():
    """Verifica o arquivo resultado.txt e o log do coordenador"""
    
    print("=" * 50)
    print("VERIFICAÇÃO DOS RESULTADOS")
    print("=" * 50)
    
    # Verificar se os arquivos existem
    if not os.path.exists('resultado.txt'):
        print("❌ Arquivo resultado.txt não encontrado!")
        return
    
    if not os.path.exists('log_coordenador.txt'):
        print("❌ Arquivo log_coordenador.txt não encontrado!")
        return
    
    # 1. VERIFICAR ARQUIVO resultado.txt
    print("\n1. VERIFICAÇÃO DO resultado.txt")
    print("-" * 30)
    
    with open('resultado.txt', 'r') as f:
        linhas = f.readlines()
    
    print(f"Total de linhas no resultado.txt: {len(linhas)}")
    
    # Contar entradas por processo
    contadores_processos = defaultdict(int)
    timestamps = []
    
    for i, linha in enumerate(linhas, 1):
        linha = linha.strip()
        if not linha:
            continue
            
        try:
            # Formato esperado: "Processo X | YYYY-MM-DD HH:MM:SS.mmm"
            partes = linha.split('|')
            processo_info = partes[0].strip()
            timestamp = partes[1].strip()
            
            processo_id = int(processo_info.split()[-1])
            contadores_processos[processo_id] += 1
            timestamps.append((processo_id, timestamp, i))
            
        except (IndexError, ValueError) as e:
            print(f"❌ Erro na linha {i}: {linha} - {e}")
    
    # Mostrar estatísticas por processo
    print("\nEntradas por processo:")
    for pid in sorted(contadores_processos.keys()):
        count = contadores_processos[pid]
        print(f"  Processo {pid}: {count} entradas")
    
    # Verificar ordem dos timestamps
    print("\nVerificação da ordem temporal:")
    problemas_ordem = 0
    for i in range(1, len(timestamps)):
        pid_atual, ts_atual, linha_atual = timestamps[i]
        pid_anterior, ts_anterior, linha_anterior = timestamps[i-1]
        
        # Verificar se o timestamp atual é maior ou igual ao anterior
        if ts_atual < ts_anterior:
            print(f"  ❌ Problema de ordem na linha {linha_atual}:")
            print(f"     Linha {linha_anterior}: Processo {pid_anterior} | {ts_anterior}")
            print(f"     Linha {linha_atual}: Processo {pid_atual} | {ts_atual}")
            problemas_ordem += 1
    
    if problemas_ordem == 0:
        print("  ✅ Todas as entradas estão em ordem temporal correta")
    
    # 2. VERIFICAR LOG DO COORDENADOR
    print("\n2. VERIFICAÇÃO DO log_coordenador.txt")
    print("-" * 40)
    
    with open('log_coordenador.txt', 'r') as f:
        logs = f.readlines()
    
    print(f"Total de entradas no log: {len(logs)}")
    
    # Analisar sequência de mensagens
    sequencia_por_processo = defaultdict(list)
    
    for log in logs:
        partes = log.strip().split(' | ')
        if len(partes) >= 4:
            timestamp, tipo, processo, direcao = partes[0], partes[1], partes[2], partes[3]
            try:
                pid = int(processo)
                sequencia_por_processo[pid].append((tipo, direcao))
            except ValueError:
                continue
    
    # Verificar padrão GRANT → RELEASE para cada processo
    print("\nVerificação do padrão GRANT → RELEASE:")
    problemas_padrao = 0
    
    for pid, sequencia in sequencia_por_processo.items():
        print(f"\nProcesso {pid}:")
        grant_count = 0
        release_count = 0
        
        for i, (tipo, direcao) in enumerate(sequencia):
            if tipo == "GRANT" and direcao == "ENVIADA":
                grant_count += 1
                print(f"  GRANT #{grant_count}")
                
            elif tipo == "RELEASE" and direcao == "RECEBIDA":
                release_count += 1
                print(f"  RELEASE #{release_count}")
                
                # Verificar se temos um GRANT para cada RELEASE
                if release_count > grant_count:
                    print(f"  ❌ RELEASE sem GRANT correspondente!")
                    problemas_padrao += 1
        
        # Verificar contagens finais
        if grant_count == release_count:
            print(f"  ✅ GRANTs: {grant_count}, RELEASEs: {release_count} - BALANCEADO")
        else:
            print(f"  ❌ GRANTs: {grant_count}, RELEASEs: {release_count} - DESBALANCEADO")
            problemas_padrao += 1
    
    # 3. RESUMO FINAL
    print("\n" + "=" * 50)
    print("RESUMO FINAL")
    print("=" * 50)
    
    total_entradas = len(linhas)
    total_processos = len(contadores_processos)
    total_logs = len(logs)
    
    print(f"• Entradas em resultado.txt: {total_entradas}")
    print(f"• Processos que escreveram: {total_processos}")
    print(f"• Entradas no log: {total_logs}")
    print(f"• Problemas de ordem temporal: {problemas_ordem}")
    print(f"• Problemas no padrão GRANT/RELEASE: {problemas_padrao}")
    
    if problemas_ordem == 0 and problemas_padrao == 0:
        print("\n🎉 TODAS AS VERIFICAÇÕES PASSARAM! O sistema funcionou corretamente.")
    else:
        print(f"\n⚠️  Foram encontrados {problemas_ordem + problemas_padrao} problema(s)")

def analisar_log_detalhado():
    """Análise mais detalhada do log do coordenador"""
    
    if not os.path.exists('log_coordenador.txt'):
        print("Arquivo log_coordenador.txt não encontrado!")
        return
    
    print("\n" + "=" * 50)
    print("ANÁLISE DETALHADA DO LOG")
    print("=" * 50)
    
    with open('log_coordenador.txt', 'r') as f:
        logs = [line.strip() for line in f if line.strip()]
    
    # Estatísticas por tipo de mensagem
    stats = defaultdict(int)
    
    for log in logs:
        partes = log.split(' | ')
        if len(partes) >= 2:
            tipo = partes[1]
            stats[tipo] += 1
    
    print("Estatísticas de mensagens:")
    for tipo, count in sorted(stats.items()):
        print(f"  {tipo}: {count}")
    
    # Mostrar sequência completa
    print("\nSequência completa de eventos:")
    for i, log in enumerate(logs[:20], 1):  # Mostrar apenas primeiros 20
        print(f"  {i:2d}. {log}")
    
    if len(logs) > 20:
        print(f"  ... e mais {len(logs) - 20} eventos")

if __name__ == "__main__":
    verificar_resultado()
    analisar_log_detalhado()