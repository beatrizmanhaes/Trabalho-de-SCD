import socket
import time
import sys
from datetime import datetime

class Processo:
    def __init__(self, processo_id, host='localhost', port=5000, msg_size=20, repeticoes=3, delay_critico=1):
        self.processo_id = processo_id
        self.host = host
        self.port = port
        self.msg_size = msg_size
        self.repeticoes = repeticoes
        self.delay_critico = delay_critico
        self.socket = None
    
    def conectar_coordenador(self):
        try:
            print(f"🔗 Processo {self.processo_id} tentando conectar em {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # Timeout de 5 segundos
            self.socket.connect((self.host, self.port))
            print(f"✅ Processo {self.processo_id} conectado ao coordenador!")
            return True
        except ConnectionRefusedError:
            print(f"❌ Processo {self.processo_id}: Coordenador recusou conexão")
            print("   💡 Verifique se o coordenador está executando na porta 5000")
            return False
        except Exception as e:
            print(f"❌ Processo {self.processo_id} erro na conexão: {e}")
            print("   💡 Execute o coordenador primeiro: python coordenador.py")
            return False
    
    def enviar_request(self):
        try:
            mensagem = f"1|{self.processo_id}|".ljust(self.msg_size, '0')
            self.socket.send(mensagem.encode('utf-8'))
            print(f"📤 Processo {self.processo_id}: REQUEST enviado")
            return True
        except Exception as e:
            print(f"❌ Processo {self.processo_id} erro ao enviar REQUEST: {e}")
            return False
    
    def enviar_release(self):
        try:
            mensagem = f"3|{self.processo_id}|".ljust(self.msg_size, '0')
            self.socket.send(mensagem.encode('utf-8'))
            print(f"📤 Processo {self.processo_id}: RELEASE enviado")
            return True
        except Exception as e:
            print(f"❌ Processo {self.processo_id} erro ao enviar RELEASE: {e}")
            return False
    
    def aguardar_grant(self):
        print(f"⏳ Processo {self.processo_id} aguardando GRANT...")
        try:
            while True:
                data = self.socket.recv(self.msg_size).decode('utf-8').strip()
                if data:
                    partes = data.split('|')
                    if len(partes) >= 2 and partes[0] == '2' and int(partes[1]) == self.processo_id:
                        print(f"✅ Processo {self.processo_id}: GRANT recebido!")
                        return True
        except Exception as e:
            print(f"❌ Processo {self.processo_id} erro ao aguardar GRANT: {e}")
            return False
    
    def executar_regiao_critica(self, iteracao):
        print(f"🔒 Processo {self.processo_id} executando região crítica (iteração {iteracao})...")
        
        try:
            # Escrever no arquivo compartilhado
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with open('resultado.txt', 'a', encoding='utf-8') as f:
                f.write(f"Processo {self.processo_id} | {timestamp} | Iteração {iteracao}\n")
            
            print(f"📝 Processo {self.processo_id} escreveu no arquivo")
            
            # Simular processamento na região crítica
            time.sleep(self.delay_critico)
            
            print(f"🔓 Processo {self.processo_id} saindo da região crítica")
            return True
        except Exception as e:
            print(f"❌ Processo {self.processo_id} erro na região crítica: {e}")
            return False
    
    def executar(self):
        if not self.conectar_coordenador():
            print("🔄 Tentando reconectar em 3 segundos...")
            time.sleep(3)
            if not self.conectar_coordenador():
                return
        
        print(f"🔄 Processo {self.processo_id} iniciando {self.repeticoes} repetições")
        
        for i in range(1, self.repeticoes + 1):
            print(f"\n🔄 Processo {self.processo_id} - Iteração {i}/{self.repeticoes}")
            
            # 1. Solicitar acesso à região crítica
            if not self.enviar_request():
                break
            
            # 2. Aguardar permissão do coordenador
            if not self.aguardar_grant():
                break
            
            # 3. Executar região crítica
            if not self.executar_regiao_critica(i):
                break
            
            # 4. Liberar acesso
            if not self.enviar_release():
                break
            
            # Esperar entre requisições
            if i < self.repeticoes:
                print(f"⏰ Processo {self.processo_id} aguardando próximo ciclo...")
                time.sleep(2)
        
        if self.socket:
            self.socket.close()
        print(f"🎉 Processo {self.processo_id} finalizado!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python processo.py <numero_processo>")
        print("Exemplo: python processo.py 1")
        sys.exit(1)
    
    try:
        processo_id = int(sys.argv[1])
        print("=" * 50)
        print(f"🚀 INICIANDO PROCESSO {processo_id}")
        print("=" * 50)
        
        processo = Processo(processo_id, repeticoes=3, delay_critico=1)
        processo.executar()
    except ValueError:
        print("Erro: O número do processo deve ser um inteiro")
    except KeyboardInterrupt:
        print(f"\nProcesso {processo_id} interrompido pelo usuário")
    except Exception as e:
        print(f"Erro no processo {processo_id}: {e}")
    
    input("Pressione Enter para sair...")