import socket
import time
import sys
from datetime import datetime

class Processo:
    def __init__(self, processo_id, host='localhost', port=5000, msg_size=20, repeticoes=3):
        self.id = processo_id
        self.host = host
        self.port = port
        self.msg_size = msg_size
        self.repeticoes = repeticoes
        self.socket = None
    
    def conectar(self):
        """Conecta ao coordenador"""
        try:
            print(f"Processo {self.id}: Conectando ao coordenador...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(10)  # Timeout de 10 segundos
            print(f"Processo {self.id}: Conectado!")
            return True
        except Exception as e:
            print(f"Processo {self.id}: Erro na conexão: {e}")
            return False
    
    def enviar_mensagem(self, tipo):
        """Envia uma mensagem ao coordenador"""
        try:
            mensagem = f"{tipo}|{self.id}|".ljust(self.msg_size, '0')
            self.socket.send(mensagem.encode())
            print(f"Processo {self.id}: Enviou {tipo}")
            return True
        except Exception as e:
            print(f"Processo {self.id}: Erro ao enviar mensagem: {e}")
            return False
    
    def esperar_grant(self):
        """Aguarda receber GRANT do coordenador"""
        print(f"Processo {self.id}: Aguardando GRANT...")
        
        try:
            while True:
                dados = self.socket.recv(self.msg_size)
                if dados:
                    mensagem = dados.decode().strip()
                    partes = mensagem.split('|')
                    
                    if len(partes) >= 2 and partes[0] == '2':
                        processo_destino = int(partes[1])
                        if processo_destino == self.id:
                            print(f"Processo {self.id}: Recebeu GRANT!")
                            return True
        except socket.timeout:
            print(f"Processo {self.id}: Timeout esperando GRANT")
            return False
        except Exception as e:
            print(f"Processo {self.id}: Erro ao esperar GRANT: {e}")
            return False
    
    def executar_regiao_critica(self, iteracao):
        """Executa a região crítica"""
        print(f"Processo {self.id}: Executando região crítica...")
        
        try:
            # Escrever no arquivo compartilhado
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open('resultado.txt', 'a') as f:
                f.write(f"Processo {self.id} | {timestamp} | Iteracao {iteracao}\n")
            
            print(f"Processo {self.id}: Escreveu no arquivo")
            
            # Simular trabalho
            time.sleep(1)
            
            return True
        except Exception as e:
            print(f"Processo {self.id}: Erro na região crítica: {e}")
            return False
    
    def executar_ciclo(self, iteracao):
        """Executa um ciclo completo"""
        print(f"\nProcesso {self.id}: Ciclo {iteracao} iniciado")
        
        # 1. Enviar REQUEST
        if not self.enviar_mensagem('1'):
            return False
        
        # 2. Esperar GRANT
        if not self.esperar_grant():
            return False
        
        # 3. Executar região crítica
        if not self.executar_regiao_critica(iteracao):
            return False
        
        # 4. Enviar RELEASE
        if not self.enviar_mensagem('3'):
            return False
        
        print(f"Processo {self.id}: Ciclo {iteracao} completo")
        return True
    
    def executar(self):
        """Executa todas as repetições do processo"""
        if not self.conectar():
            return
        
        print(f"Processo {self.id}: Iniciando {self.repeticoes} ciclos")
        
        for i in range(1, self.repeticoes + 1):
            if not self.executar_ciclo(i):
                print(f"Processo {self.id}: Erro no ciclo {i}")
                break
            
            # Esperar entre ciclos
            if i < self.repeticoes:
                time.sleep(0.5)
        
        # Fechar conexão
        if self.socket:
            self.socket.close()
        
        print(f"Processo {self.id}: Finalizado")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python processo.py <id_processo>")
        print("Exemplo: python processo.py 1")
        sys.exit(1)
    
    try:
        pid = int(sys.argv[1])
        processo = Processo(pid, repeticoes=3)
        processo.executar()
    except ValueError:
        print("Erro: ID do processo deve ser um número")
    except Exception as e:
        print(f"Erro: {e}")