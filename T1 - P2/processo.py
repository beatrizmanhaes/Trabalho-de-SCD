import socket, sys, time, datetime

# Configurações do Processo
HOST, PORT, F_SIZE = '127.0.0.1', 5000, 10
REPETICOES, K_SLEEP = 5, 1 # r = 5, k = 1 segundo

if len(sys.argv) < 2: sys.exit("Uso: python processo.py <ID>")
pid = sys.argv[1]

sock = None
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    def enviar(tipo): 
        """Envia mensagem de tamanho fixo F."""
        sock.send(f"{tipo}|{pid}|".ljust(F_SIZE, '0').encode()) 

    for i in range(REPETICOES):
        enviar('1') # 1. REQUEST
        
        # 2. Espera GRANT
        while True: 
            data = sock.recv(F_SIZE).decode()
            if data.startswith('2'): break

        # 3. Região Crítica (RC)
        with open('resultado.txt', 'a') as f:
            ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            f.write(f"Processo {pid} | {ts}\n")
        
        time.sleep(K_SLEEP) # Aguarda k segundos
        
        enviar('3') # 4. RELEASE

except ConnectionRefusedError:
    print(f"Processo {pid}: Erro de conexao. Certifique-se que o Coordenador esta rodando.")
except Exception as e:
    print(f"Processo {pid}: Erro durante a execucao: {e}")
finally:
    if sock:
        sock.close()