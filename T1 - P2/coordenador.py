import socket
import threading
import time
import os
import sys
from collections import deque
from datetime import datetime

class Coordenador:
    def __init__(self, host='localhost', port=5000, msg_size=20):
        self.host = host
        self.port = port
        self.msg_size = msg_size
        
        # Estruturas críticas - protegidas por lock
        self.fila_espera = deque()  # Fila de processos esperando
        self.processos_conectados = {}  # ID -> socket
        self.contadores = {}  # Contagem de acessos por processo
        self.processo_na_rc = None  # Processo atual na região crítica
        
        # Lock principal para sincronização
        self.lock = threading.Lock()
        
        # Estado do sistema
        self.executando = True
        self.log_file = "log_coordenador.txt"
        
        print("Coordenador inicializado")
        print(f"Escutando em {host}:{port}")
    
    def registrar_log(self, tipo, processo, direcao):
        """Registra um evento no log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        mensagem = f"{timestamp} | {tipo} | {processo} | {direcao}"
        
        # Escrever no arquivo
        with open(self.log_file, 'a') as f:
            f.write(mensagem + '\n')
        
        # Mostrar no console
        print(mensagem)
    
    def enviar_grant(self, processo_id):
        """Envia mensagem GRANT para um processo"""
        if processo_id in self.processos_conectados:
            try:
                mensagem = f"2|{processo_id}|".ljust(self.msg_size, '0')
                self.processos_conectados[processo_id].send(mensagem.encode())
                self.registrar_log("GRANT", processo_id, "ENVIADA")
                print(f"Concedido acesso ao Processo {processo_id}")
                return True
            except Exception as e:
                print(f"Erro ao enviar GRANT para Processo {processo_id}: {e}")
                return False
        else:
            print(f"Processo {processo_id} não está conectado")
            return False
    
    def processar_mensagem(self, mensagem, processo_id):
        """Processa uma mensagem recebida de um processo"""
        try:
            partes = mensagem.split('|')
            if len(partes) < 2:
                return
            
            tipo = partes[0]
            
            with self.lock:
                if tipo == '1':  # REQUEST
                    self.registrar_log("REQUEST", processo_id, "RECEBIDA")
                    print(f"Processo {processo_id} solicitou acesso")
                    
                    # Adicionar à fila se não estiver
                    if processo_id not in self.fila_espera:
                        self.fila_espera.append(processo_id)
                        print(f"Fila atual: {list(self.fila_espera)}")
                    
                    # Se nenhum processo está na RC, conceder acesso
                    if self.processo_na_rc is None and self.fila_espera[0] == processo_id:
                        self.processo_na_rc = processo_id
                        self.enviar_grant(processo_id)
                
                elif tipo == '3':  # RELEASE
                    self.registrar_log("RELEASE", processo_id, "RECEBIDA")
                    print(f"Processo {processo_id} liberou a região crítica")
                    
                    # Atualizar contador
                    if processo_id not in self.contadores:
                        self.contadores[processo_id] = 0
                    self.contadores[processo_id] += 1
                    
                    # Liberar região crítica
                    if self.processo_na_rc == processo_id:
                        self.processo_na_rc = None
                    
                    # Remover da fila (deve ser o primeiro)
                    if self.fila_espera and self.fila_espera[0] == processo_id:
                        self.fila_espera.popleft()
                        print(f"Fila após liberação: {list(self.fila_espera)}")
                    
                    # Conceder acesso ao próximo da fila, se houver
                    if self.fila_espera and self.processo_na_rc is None:
                        proximo = self.fila_espera[0]
                        self.processo_na_rc = proximo
                        self.enviar_grant(proximo)
        
        except Exception as e:
            print(f"Erro ao processar mensagem do Processo {processo_id}: {e}")
    
    def interface_usuario(self):
        """Interface de comandos do coordenador"""
        while self.executando:
            try:
                print("\n" + "="*40)
                print("COMANDOS DO COORDENADOR")
                print("="*40)
                print("1. Ver fila de espera")
                print("2. Ver processo na região crítica")
                print("3. Ver contadores de acesso")
                print("4. Sair")
                print("-"*40)
                
                opcao = input("Escolha uma opção: ")
                
                with self.lock:
                    if opcao == '1':
                        print(f"\nFila de espera: {list(self.fila_espera)}")
                        print(f"Total na fila: {len(self.fila_espera)}")
                    
                    elif opcao == '2':
                        if self.processo_na_rc:
                            print(f"\nProcesso na região crítica: {self.processo_na_rc}")
                        else:
                            print("\nNenhum processo na região crítica")
                    
                    elif opcao == '3':
                        print("\nContadores de acesso:")
                        if self.contadores:
                            for pid, count in sorted(self.contadores.items()):
                                print(f"  Processo {pid}: {count} vez(es)")
                        else:
                            print("  Nenhum acesso registrado")
                    
                    elif opcao == '4':
                        print("\nEncerrando coordenador...")
                        self.executando = False
                        os._exit(0)
                    
                    else:
                        print("\nOpção inválida")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Erro na interface: {e}")
    
    def lidar_com_processo(self, conexao, endereco, processo_id):
        """Gerencia a comunicação com um processo"""
        with self.lock:
            self.processos_conectados[processo_id] = conexao
        
        print(f"Processo {processo_id} conectado de {endereco}")
        
        try:
            while self.executando:
                try:
                    dados = conexao.recv(self.msg_size)
                    if not dados:
                        break
                    
                    mensagem = dados.decode().strip()
                    if mensagem:
                        self.processar_mensagem(mensagem, processo_id)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Erro ao receber do Processo {processo_id}: {e}")
                    break
        
        except Exception as e:
            print(f"Erro na conexão com Processo {processo_id}: {e}")
        
        finally:
            # Limpeza
            conexao.close()
            
            with self.lock:
                if processo_id in self.processos_conectados:
                    del self.processos_conectados[processo_id]
                
                # Remover da fila
                if processo_id in self.fila_espera:
                    self.fila_espera.remove(processo_id)
                    print(f"Processo {processo_id} removido da fila")
                
                # Se era o processo na RC, liberar
                if self.processo_na_rc == processo_id:
                    self.processo_na_rc = None
                    print(f"Processo {processo_id} removido da região crítica")
            
            print(f"Processo {processo_id} desconectado")
            
            # Tentar conceder ao próximo
            with self.lock:
                if self.fila_espera and self.processo_na_rc is None:
                    proximo = self.fila_espera[0]
                    self.processo_na_rc = proximo
                    self.enviar_grant(proximo)
    
    def iniciar_servidor(self):
        """Inicia o servidor para aceitar conexões"""
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.settimeout(1)
        
        try:
            servidor.bind((self.host, self.port))
            servidor.listen(5)
            
            processo_id = 1
            
            while self.executando:
                try:
                    conexao, endereco = servidor.accept()
                    conexao.settimeout(1)
                    
                    # Criar thread para o processo
                    thread = threading.Thread(
                        target=self.lidar_com_processo,
                        args=(conexao, endereco, processo_id),
                        daemon=True
                    )
                    thread.start()
                    
                    processo_id += 1
                
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.executando:
                        print(f"Erro ao aceitar conexão: {e}")
        
        except Exception as e:
            print(f"Erro no servidor: {e}")
        
        finally:
            servidor.close()
    
    def iniciar(self):
        """Inicia o coordenador"""
        print("="*50)
        print("SISTEMA DE EXCLUSÃO MÚTUA - COORDENADOR")
        print("="*50)
        
        # Limpar arquivos antigos
        open(self.log_file, 'w').close()
        open('resultado.txt', 'w').close()
        
        # Iniciar thread do servidor
        servidor_thread = threading.Thread(target=self.iniciar_servidor, daemon=True)
        servidor_thread.start()
        
        # Iniciar interface
        interface_thread = threading.Thread(target=self.interface_usuario, daemon=True)
        interface_thread.start()
        
        # Loop principal
        try:
            while self.executando:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nCoordenador interrompido")
        finally:
            self.executando = False
            print("Coordenador finalizado")

if __name__ == "__main__":
    try:
        coordenador = Coordenador()
        coordenador.iniciar()
    except Exception as e:
        print(f"Erro fatal: {e}")