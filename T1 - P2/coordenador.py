import socket, threading, time, queue, sys, os
from datetime import datetime

# configurações do Sistema
HOST, PORT, F_SIZE = '127.0.0.1', 5000, 10 # endIP, porta e tamanho fixo das mensagens

# variaveis globais e lock de sincronização
log_lock = threading.Lock() # trava para garantir escrita de log segura 
fila, sockets, lock, req_atual = [], {}, threading.Lock(), None

"""
sockets: dicionario que mapeia o PID ao seu objeto de conexão para permitir o envio de mensagens
lock: protege as variaveis globais (fila, sockets e req_atual)
req_atual: armazena o PID do processo que está atualmente na região critica (RC)
fila: LISTA que armazena os PIDs em espera.
"""

def log(tipo, pid, dir):
    # função de log thread-safe que registra eventos em arquivo
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    mensagem = f"{timestamp}|{tipo}|{pid}|{dir}"
    
    print(mensagem) 
    with log_lock:
        with open('log_coordenador.txt', 'a') as f:
            f.write(mensagem + '\n')

def handle(conn, addr): 
    global req_atual 
    
    pid = None
    try:
        while True:
            data = conn.recv(F_SIZE) # recebe os dados do socket
            if not data: break 
            
            mensagem = data.decode().strip() # converte os bytes recebidos em string
            tipo, pid_str, _ = mensagem.split('|')
            pid = pid_str
            
            with lock: 
                sockets[pid] = conn # armazena do dicionario o socket relacionado ao processo
            
            if tipo == '1': # REQUEST (if m.request)
                log('REQUEST', pid, 'RECEBIDA')
                
                with lock:
                    if req_atual is None: 
                        req_atual = pid # OCUPADA RC
                        fila.append(pid) # Adiciona à fila
                        
                        try:
                            # Envia GRANT (send(m.process, Grant))
                            sockets[pid].send(f"2|{pid}|".ljust(F_SIZE, '0').encode()) 
                            log('GRANT', pid, 'ENVIADA')
                        except: 
                            # Se falhar, libera a RC e remove da fila 
                            req_atual = None 
                            if pid in fila: fila.remove(pid)
                    else: 
                        # RC OCUPADA, apenas adiciona à fila de espera (Q.add(m.process))
                        fila.append(pid)
                        
            elif tipo == '3': # RELEASE (if m.release)
                log('RELEASE', pid, 'RECEBIDA')
                
                with lock: 
                    if req_atual == pid: 
                        
                        # 1. Libera a RC 
                        req_atual = None 
                        if pid in fila: fila.remove(pid) # Remove o PID liberado da fila
                        
                        # 2. Verifica se há processos esperando (!Q.empty)
                        if fila: 
                            prox = fila[0] # Pega o próximo processo (process = Q.head())
                            
                            if prox in sockets: 
                                req_atual = prox # OCUPADA RC pelo próximo processo
                                try:
                                    # Envia GRANT
                                    sockets[prox].send(f"2|{prox}|".ljust(F_SIZE, '0').encode()) 
                                    log('GRANT', prox, 'ENVIADA')
                                except: 
                                    # Se falhar o envio, libera a RC e remove da fila
                                    req_atual = None
                                    if prox in fila: fila.remove(prox)
                    else:
                        pass # Ignora RELEASE de quem não está na RC

    except: 
        pass
    finally: # Garante que o socket seja fechado e removido do estado global ao sair do loop
        if pid:
            with lock: 
                sockets.pop(pid, None)
                if pid in fila: fila.remove(pid) # Remove da fila se desconectar
        conn.close()


def interface(): 
    # interface simples para inspeção e encerramento
    print("Coordenador Interface: 1-Fila, 2-Ativo, 3-Sair")
    while True:
        try:
            cmd = input()
            if cmd == '1': 
                with lock: print(f"Fila: {fila}") 
            elif cmd == '2': 
                with lock: print(f"Ativo: {req_atual}")
            elif cmd == '3': 
                print("Encerrando...")
                os._exit(0)
        except: 
            break

# Ini cia o Coordenador
if __name__ == "__main__":
    try:
        # Limpa arquivos de log
        for f in ['resultado.txt', 'log_coordenador.txt']:
            if os.path.exists(f): os.remove(f)
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # cria socket principal
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reinicia servidor automaticamente apos encerrado
        server.settimeout(0.5) 
        server.bind((HOST, PORT))
        server.listen()
        
        # Inicia apenas a thread de interface
        threading.Thread(target=interface, daemon=True).start()
        print(f"Coordenador escutando em {HOST}:{PORT}")

        while True:
            try:
                conn, addr = server.accept() # aceita novas conexões
                # conexão com socket e endereço (IP e porta)
                threading.Thread(target=handle, args=(conn, addr), daemon=True).start() # inicia uma thread handle() para cada nova conexão (cliente)
            except socket.timeout: 
                continue
            except:
                break
    except Exception as e: # tratamento de erros
        print(f"Erro fatal na inicializacao: {e}")
    finally:
        if 'server' in locals():
            server.close()