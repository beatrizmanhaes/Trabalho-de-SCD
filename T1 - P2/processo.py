import socket, sys, time, datetime

HOST, PORT, F_SIZE = '127.0.0.1', 5000, 10
REPETICOES, K_SLEEP = 5, 1 # r e k

if len(sys.argv) < 2: sys.exit("Uso: processo.py <ID>")
pid = sys.argv[1]

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    def enviar(tipo): sock.send(f"{tipo}|{pid}|".ljust(F_SIZE, '0').encode()) 

    for i in range(REPETICOES):
        enviar('1') # REQUEST
        
        while True: # Espera GRANT
            # Espera a mensagem de F_SIZE bytes
            data = sock.recv(F_SIZE).decode()
            if data.startswith('2'): break

        # Regiao Critica
        with open('resultado.txt', 'a') as f:
            ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            f.write(f"Processo {pid} | {ts}\n")
        
        time.sleep(K_SLEEP) 
        enviar('3') # RELEASE

except ConnectionRefusedError:
    print(f"Processo {pid}: Erro de conexao. Certifique-se que o Coordenador esta rodando.")
except Exception as e:
    print(f"Processo {pid}: Erro durante a execucao: {e}")
finally:
    if 'sock' in locals():
        sock.close()