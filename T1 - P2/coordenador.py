import socket, threading, time, queue, sys, os
from datetime import datetime

# configurações do Sistema
HOST, PORT, F_SIZE = '127.0.0.1', 5000, 10 # endIP, porta e tamanho fixo das mensagens

# variaveis globais e lock de sincronização
log_lock = threading.Lock() # trava para garantir escrita de log segura 
fila, sockets, lock, req_atual = queue.Queue(), {}, threading.Lock(), None

"""sockets: dicionario que mapeia o PID ao seu objeto de conexão para permitir o envio de mensagens
lock: protege as variaveis fila, sockets e req_atual
req_atual: armazena o PID do processo que está atualmente na região critica"""

def log(tipo, pid, dir):
    # função de log thread-safe que registra eventos em arquivo
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    mensagem = f"{timestamp}|{tipo}|{pid}|{dir}"
    
    print(mensagem) 
    with log_lock:
        with open('log_coordenador.txt', 'a') as f:
            f.write(mensagem + '\n')

def handle(conn, addr): 
    # gerencia a comunicação e o ciclo de vida de um processo cliente na fila
    pid = None
    try:
        while True:
            data = conn.recv(F_SIZE) # recebe os dados do socket
            if not data: break 
            
            mensagem = data.decode().strip() # converte os bytes recebidos em string
            tipo, pid_str, _ = mensagem.split('|')
            pid = pid_str
            
            with lock: sockets[pid] = conn # armazena do dicionario o socket relacionado ao processo
            
            if tipo == '1': # REQUEST
                # LOG NATURAL: registra a REQUEST assim que ela é recebida
                log('REQUEST', pid, 'RECEBIDA') 
                fila.put(pid)
            elif tipo == '3': # RELEASE
                log('RELEASE', pid, 'RECEBIDA')
                with lock: 
                    global req_atual
                    if req_atual == pid: # se o processo que enviou o release for o mesmo que detinha o acesso 
                        req_atual = None # RC LIBERADA

    except: 
        pass
    finally: # garante que o socket seja fechado e removido do estado global ao sair do loop
        if pid:
            with lock: sockets.pop(pid, None)
        conn.close()

def core():
    # thread do Algoritmo Centralizado que garante o controle da RC
    global req_atual
    while True:
        if not fila.empty():
            with lock: 
                livre = (req_atual is None) # RC livre se req_atual for None
            
            if livre:
                try:
                    prox = fila.get(block=False) # pega o proximo processo da fila
                except queue.Empty:
                    continue # já foi removido por outra thread (imprevisto raro)
                
                with lock:
                    if prox in sockets: # confirma se o processo ainda está conectado
                        req_atual = prox # OCUPADA RC (guarda o PID que entrará)
                        try:
                            # envia GRANT
                            sockets[prox].send(f"2|{prox}|".ljust(F_SIZE, '0').encode()) 
                            log('GRANT', prox, 'ENVIADA')
                        except: 
                            req_atual = None # se falhar o envio, libera a RC
        time.sleep(0.001)

def interface(): 
    # interface simples para inspeção e encerramento
    print("Coordenador Interface: 1-Fila, 2-Ativo, 3-Sair")
    while True:
        try:
            cmd = input()
            if cmd == '1': 
                with lock: print(f"Fila: {list(fila.queue)}")
            elif cmd == '2': 
                with lock: print(f"Ativo: {req_atual}")
            elif cmd == '3': 
                print("Encerrando...")
                os._exit(0)
        except: 
            break

# Inicia o Coordenador
if __name__ == "__main__":
    try:
        for f in ['resultado.txt', 'log_coordenador.txt']:
            if os.path.exists(f): os.remove(f)
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # cria socket principal
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reinicia servidor automaticamente apos encerrado
        server.settimeout(0.5) 
        server.bind((HOST, PORT))
        server.listen()
        
        # inicia as threads de controle e interface
        threading.Thread(target=core, daemon=True).start()
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