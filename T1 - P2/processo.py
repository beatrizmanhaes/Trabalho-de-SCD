import socket, sys, time, datetime, os

# configurações do Processo
HOST, PORT, F_SIZE = '127.0.0.1', 5000, 10 # endIP, porta e tamanho fixo das mensagens 
REPETICOES, K_SLEEP = 3, 1 # r = 3, k = 1 segundo # numero de vezes que o processor tentará entrar na RC, tempo que passará na RC

# requer que o ID do processo seja passado como argumento na linha de comando
if len(sys.argv) < 2: sys.exit("Uso: python processo.py <ID>")
pid = sys.argv[1]

sock = None
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT)) # conecta o socket criado ao coordenador

    def enviar(tipo): 
        # envia mensagem de tamanho fixo
        sock.send(f"{tipo}|{pid}|".ljust(F_SIZE, '0').encode()) 

    for i in range(REPETICOES): # implementa o ciclo de vida da exclusão mutua
        enviar('1') # 1. REQUEST
        
        # 2. espera GRANT
        while True: 
            data = sock.recv(F_SIZE).decode()
            if data.startswith('2'): break

        # 3. região crítica (RC)
        with open('resultado.txt', 'a') as f:
            ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            f.write(f"Processo {pid} | {ts}\n") # retorna quanto tempo um processo ficou na RC 
        
        time.sleep(K_SLEEP) # aguarda k segundos
        
        enviar('3') # 4. RELEASE

# tratamento de erros
except ConnectionRefusedError:
    print(f"Processo {pid}: Erro de conexao. Certifique-se que o Coordenador esta rodando.")
except Exception as e:
    print(f"Processo {pid}: Erro durante a execucao: {e}")
finally:
    if sock:
        sock.close()