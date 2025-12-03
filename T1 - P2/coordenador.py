import socket, threading, time, queue, sys, os
from datetime import datetime

# Configurações do Sistema
HOST, PORT, F_SIZE = '127.0.0.1', 5000, 10
LOG_FILE = 'log_coordenador.txt'

# Estado Global e Locks de Sincronização
log_lock = threading.Lock() 
fila, sockets, lock, req_atual = queue.Queue(), {}, threading.Lock(), None

def log(tipo, pid, dir):
    """Função de log thread-safe com escrita imediata em arquivo."""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    mensagem = f"{timestamp}|{tipo}|{pid}|{dir}"
    
    print(mensagem) 
    with log_lock:
        with open(LOG_FILE, 'a') as f:
            f.write(mensagem + '\n')

def handle(conn, addr):
    """Gerencia a comunicação e o ciclo de vida de um processo cliente."""
    pid = None
    try:
        while True:
            data = conn.recv(F_SIZE) 
            if not data: break
            
            mensagem = data.decode().strip()
            tipo, pid_str, _ = mensagem.split('|')
            pid = pid_str
            
            with lock: sockets[pid] = conn
            
            if tipo == '1': # REQUEST
                # LOG NATURAL: Registra a REQUEST assim que ela é recebida.
                log('REQUEST', pid, 'RECEBIDA') 
                fila.put(pid)
            elif tipo == '3': # RELEASE
                log('RELEASE', pid, 'RECEBIDA')
                with lock: 
                    global req_atual
                    if req_atual == pid: 
                        req_atual = None # RC LIBERADA

    except: 
        pass
    finally:
        if pid:
            with lock: sockets.pop(pid, None)
        conn.close()

def core():
    """Thread do Algoritmo Centralizado. Garante o controle da RC."""
    global req_atual
    while True:
        if not fila.empty():
            with lock: 
                livre = (req_atual is None)
            
            if livre:
                try:
                    prox = fila.get(block=False) 
                except queue.Empty:
                    continue
                
                with lock:
                    if prox in sockets:
                        req_atual = prox # RC OCUPADA
                        try:
                            # Envia GRANT
                            sockets[prox].send(f"2|{prox}|".ljust(F_SIZE, '0').encode()) 
                            log('GRANT', prox, 'ENVIADA')
                        except: 
                            req_atual = None
        time.sleep(0.001)

def interface(): 
    """Interface simples para inspeção e encerramento."""
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
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.settimeout(0.5) 
        server.bind((HOST, PORT))
        server.listen()
        
        threading.Thread(target=core, daemon=True).start()
        threading.Thread(target=interface, daemon=True).start()
        print(f"Coordenador escutando em {HOST}:{PORT}")

        while True:
            try:
                conn, addr = server.accept()
                threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
            except socket.timeout:
                continue
            except:
                break
    except Exception as e:
        print(f"Erro fatal na inicializacao: {e}")
    finally:
        if 'server' in locals():
            server.close()