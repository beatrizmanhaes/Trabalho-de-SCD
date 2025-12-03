import socket
import threading
import time
import os
import sys
from collections import deque, defaultdict
from datetime import datetime

class Coordenador:
    def __init__(self, host='localhost', port=5000, msg_size=20):
        self.host = host
        self.port = port
        self.msg_size = msg_size
        
        # Estruturas de dados compartilhadas - PROTEGIDAS por locks
        self.fila_requests = deque()
        self.contador_processos = defaultdict(int)
        self.sockets_processos = {}
        
        # Mecanismos de exclusão mútua
        self.lock_fila = threading.Lock()        # Para a fila de requests
        self.lock_contadores = threading.Lock()  # Para os contadores
        self.lock_sockets = threading.Lock()     # Para a lista de sockets
        self.lock_log = threading.Lock()         # Para o arquivo de log
        
        self.log_file = "log_coordenador.txt"
        self.executando = True
        
        print("🔒 Coordenador multi-thread inicializado com mecanismos de sincronização")

    def log_message(self, tipo, processo, direcao):
        """Thread-safe logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with self.lock_log:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} | {tipo} | {processo} | {direcao}\n")

    def processar_mensagem(self, mensagem, processo_id):
        """Processa mensagens recebidas dos processos - Thread-safe"""
        try:
            partes = mensagem.split('|')
            if len(partes) < 2:
                return
                
            tipo_msg = partes[0]
            
            if tipo_msg == '1':  # REQUEST
                with self.lock_fila:
                    if processo_id not in self.fila_requests:
                        self.fila_requests.append(processo_id)
                        print(f"📥 REQUEST do Processo {processo_id} - Fila: {list(self.fila_requests)}")
                    self.log_message("REQUEST", processo_id, "RECEBIDA")
                
                # Verificar se pode conceder acesso imediatamente
                with self.lock_fila:
                    if self.fila_requests and self.fila_requests[0] == processo_id:
                        self.enviar_grant(processo_id)
                        
            elif tipo_msg == '3':  # RELEASE
                with self.lock_fila:
                    if self.fila_requests and self.fila_requests[0] == processo_id:
                        processo_liberado = self.fila_requests.popleft()
                        
                        with self.lock_contadores:
                            self.contador_processos[processo_id] += 1
                        
                        self.log_message("RELEASE", processo_id, "RECEBIDA")
                        print(f"✅ RELEASE do Processo {processo_id} - Fila: {list(self.fila_requests)}")
                        
                    # Concede acesso ao próximo da fila
                    if self.fila_requests:
                        proximo = self.fila_requests[0]
                        self.enviar_grant(proximo)
                        
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")

    def enviar_grant(self, processo_id):
        """Envia GRANT para um processo - Thread-safe"""
        mensagem = f"2|{processo_id}|".ljust(self.msg_size, '0')
        
        with self.lock_sockets:
            if processo_id in self.sockets_processos:
                try:
                    self.sockets_processos[processo_id].send(mensagem.encode('utf-8'))
                    self.log_message("GRANT", processo_id, "ENVIADA")
                    print(f"🎯 GRANT enviado para Processo {processo_id}")
                except Exception as e:
                    print(f"❌ Erro ao enviar GRANT para processo {processo_id}: {e}")

    def interface_thread(self):
        """Thread para interface do usuário - Comandos do terminal"""
        while self.executando:
            try:
                print("\n" + "="*50)
                print("💻 INTERFACE DO COORDENADOR - COMANDOS DISPONÍVEIS:")
                print("="*50)
                comando = input("[1] Ver Fila | [2] Ver Contadores | [3] Sair\n> ")
                
                if comando == '1':
                    with self.lock_fila:
                        fila_atual = list(self.fila_requests)
                    print(f"📋 Fila atual de requests: {fila_atual}")
                    
                elif comando == '2':
                    with self.lock_contadores:
                        contadores = dict(self.contador_processos)
                    
                    print("📊 Contadores de processos atendidos:")
                    if contadores:
                        for pid, count in sorted(contadores.items()):
                            print(f"   Processo {pid}: {count} vezes")
                    else:
                        print("   Nenhum processo foi atendido ainda")
                        
                elif comando == '3':
                    print("👋 Encerrando coordenador...")
                    self.executando = False
                    os._exit(0)
                    
            except KeyboardInterrupt:
                print("\n🛑 Interface interrompida")
                break
            except Exception as e:
                print(f"❌ Erro na interface: {e}")

    def handle_processo(self, conn, addr, processo_id):
        """Thread para lidar com cada processo conectado"""
        # Registrar socket do processo
        with self.lock_sockets:
            self.sockets_processos[processo_id] = conn
        
        print(f"✅ Processo {processo_id} conectado de {addr}")
        print(f"🧵 Thread criada para Processo {processo_id}")
        
        try:
            while self.executando:
                try:
                    data = conn.recv(self.msg_size)
                    if not data:
                        break  # Conexão fechada
                    
                    mensagem = data.decode('utf-8').strip()
                    if mensagem:
                        print(f"📨 Mensagem de {processo_id}: {mensagem}")
                        self.processar_mensagem(mensagem, processo_id)
                        
                except socket.timeout:
                    continue  # Timeout normal, continuar verificando
                except Exception as e:
                    if self.executando:
                        print(f"❌ Erro ao receber dados do Processo {processo_id}: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Erro na thread do Processo {processo_id}: {e}")
        finally:
            # Limpeza ao desconectar
            conn.close()
            with self.lock_sockets:
                if processo_id in self.sockets_processos:
                    del self.sockets_processos[processo_id]
            
            # Remover da fila se estiver nela
            with self.lock_fila:
                if processo_id in self.fila_requests:
                    self.fila_requests.remove(processo_id)
                    print(f"🗑️  Processo {processo_id} removido da fila (desconectado)")
            
            print(f"🔌 Processo {processo_id} desconectado")

    def aceitar_conexoes_thread(self):
        """Thread principal para aceitar conexões de processos"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(2.0)  # Timeout para verificar se ainda está executando
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(10)  # Até 10 conexões pendentes
            print(f"🎯 Coordenador ouvindo em {self.host}:{self.port}")
            print("🟢 Aguardando conexões de processos...")
            print("💡 Execute 'python processo.py 1' em outro terminal")
            
            processo_counter = 1
            
            while self.executando:
                try:
                    conn, addr = server_socket.accept()
                    conn.settimeout(1.0)  # Timeout para recebimento de dados
                    
                    # Criar thread para cada processo
                    thread = threading.Thread(
                        target=self.handle_processo, 
                        args=(conn, addr, processo_counter),
                        name=f"ProcessoHandler-{processo_counter}",
                        daemon=True
                    )
                    thread.start()
                    
                    processo_counter += 1
                    
                except socket.timeout:
                    continue  # Timeout normal, verificar se ainda está executando
                except OSError as e:
                    if self.executando:
                        print(f"❌ Erro de socket: {e}")
                    break
                except Exception as e:
                    if self.executando:
                        print(f"❌ Erro ao aceitar conexão: {e}")
                    
        except Exception as e:
            print(f"💥 Erro no servidor: {e}")
        finally:
            server_socket.close()
            print("🔒 Socket do servidor fechado")

    def iniciar(self):
        """Método principal para iniciar o coordenador multi-thread"""
        print("=" * 60)
        print("🚀 SISTEMA DE EXCLUSÃO MÚTUA - COORDENADOR MULTI-THREAD")
        print("=" * 60)
        print("📝 Características:")
        print("   • Thread para aceitar conexões")
        print("   • Thread para interface de comandos") 
        print("   • Uma thread por processo conectado")
        print("   • Mecanismos de sincronização: Locks")
        print("=" * 60)
        
        # Limpar arquivos antigos
        with self.lock_log:
            open(self.log_file, 'w', encoding='utf-8').close()
            open('resultado.txt', 'w', encoding='utf-8').close()
        print("🧹 Arquivos antigos limpos")
        
        # Iniciar thread para aceitar conexões
        conexoes_thread = threading.Thread(
            target=self.aceitar_conexoes_thread, 
            name="AceitarConexoes",
            daemon=True
        )
        conexoes_thread.start()
        print("🔧 Thread de aceitação de conexões iniciada")
        
        # Iniciar thread para interface do usuário
        interface_thread = threading.Thread(
            target=self.interface_thread, 
            name="InterfaceUsuario",
            daemon=True
        )
        interface_thread.start()
        print("🎮 Thread de interface iniciada")
        
        # Manter thread principal ativa
        try:
            while self.executando:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Coordenador interrompido pelo usuário")
            self.executando = False

if __name__ == "__main__":
    try:
        coordenador = Coordenador()
        coordenador.iniciar()
    except Exception as e:
        print(f"💥 Erro fatal: {e}")
    finally:
        print("👋 Coordenador finalizado")