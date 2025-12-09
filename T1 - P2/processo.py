import socket, sys, time, datetime, os

# Configurações do Processo
HOST, PORT, F_SIZE = '127.0.0.1', 5000, 10 # endIP, porta e tamanho fixo das mensagens 
# K_SLEEP permanece fixo, mas REPETICOES agora é lido de sys.argv
K_SLEEP = 1 # k = 1 segundo # tempo que passará na RC

# Requer que o ID do processo e o número de repetições (r) sejam passados como argumentos
if len(sys.argv) != 3: 
    sys.exit("Uso: python processo.py <ID> <r_repeticoes>")

pid = sys.argv[1] # Armazena o ID do processo
try:
    # REPETICOES é lido do segundo argumento (r)
    REPETICOES = int(sys.argv[2]) 
    # numero de vezes que o processo tentará entrar na RC
except ValueError:
    sys.exit("O segundo argumento (r_repeticoes) deve ser um número inteiro.")

sock = None
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT)) # conecta o socket criado ao coordenador

    def enviar(tipo): 
        # envia mensagem de tamanho fixo
        sock.send(f"{tipo}|{pid}|".ljust(F_SIZE, '0').encode()) 

    for i in range(REPETICOES): # implementa o ciclo de vida da exclusão mutua (r vezes)
        enviar('1') # 1. REQUEST
        
        # 2. espera GRANT
        while True: 
            data = sock.recv(F_SIZE).decode()
            if data.startswith('2'): break

        # 3. região crítica (RC)
        with open('resultado.txt', 'a') as f:
            ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            f.write(f"Processo {pid} | {ts}\n") # registra o PID e o timestamp de acesso à RC
        
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