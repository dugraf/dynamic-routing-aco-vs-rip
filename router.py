import socket
import json
import time
import threading
import random
import os
from collections import defaultdict
from datetime import datetime
import pytz

# Configurar fuso horário
TIMEZONE = pytz.timezone('America/Sao_Paulo')

def get_current_time():
    return datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

# Carregar configuração
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    print(f"[{get_current_time()}] Configuração carregada com sucesso: {config}")
except FileNotFoundError:
    print(f"[{get_current_time()}] Erro: Arquivo config.json não encontrado")
    exit(1)
except json.JSONDecodeError:
    print(f"[{get_current_time()}] Erro: Formato inválido no arquivo config.json")
    exit(1)

# Parâmetros de temporização e ACO
HELLO_INTERVAL = float(os.getenv("HELLO_INTERVAL", config.get("hello_interval", 2)))
UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL", config.get("update_interval", 5)))
CHECK_INTERVAL = float(os.getenv("CHECK_INTERVAL", config.get("check_interval", 15)))
PHEROMONE_INIT = float(os.getenv("PHEROMONE_INIT", config.get("pheromone_init", 1.0)))
EVAPORATION_RATE = float(os.getenv("EVAPORATION_RATE", config.get("evaporation_rate", 0.1)))
ALPHA = float(os.getenv("ALPHA", config.get("alpha", 1.0)))
BETA = float(os.getenv("BETA", config.get("beta", 2.0)))
Q = float(os.getenv("Q", config.get("q", 100.0)))

ROUTER_ID = config["router_id"]
IP = config["ip"]
PORT = config["port"]
NEIGHBORS = config["neighbors"]

# Tabelas
pheromone_table = defaultdict(lambda: defaultdict(lambda: PHEROMONE_INIT))
routing_table = defaultdict(lambda: {"next_hop": None, "metric": float("inf"), "timestamp": 0})

# Inicializar tabela de roteamento com o próprio roteador
routing_table[IP] = {"next_hop": IP, "metric": 0, "timestamp": time.time()}

def measure_latency(destination):
    """Medir latência para um destino usando ping."""
    try:
        result = os.popen(f"ping -c 1 {destination}").read()
        latency = float(result.split("time=")[1].split(" ms")[0])
        return latency if latency > 0 else 0.1
    except:
        return float("inf")

def calculate_probabilities(dest):
    """Calcula probabilidades para escolher o próximo salto."""
    probabilities = {}
    total = 0.0
    for next_hop in NEIGHBORS:
        if next_hop in pheromone_table[dest]:
            latency = measure_latency(next_hop)
            heuristic = 1.0 / latency if latency != float("inf") else 0.0
            probabilities[next_hop] = (pheromone_table[dest][next_hop] ** ALPHA) * (heuristic ** BETA)
            total += probabilities[next_hop]
    
    if total == 0:
        return {next_hop: 1.0 / len(NEIGHBORS) for next_hop in NEIGHBORS}
    
    return {next_hop: prob / total for next_hop, prob in probabilities.items()}

def choose_next_hop(dest):
    """Escolhe o próximo salto com base nas probabilidades."""
    probabilities = calculate_probabilities(dest)
    if not probabilities:
        return random.choice(NEIGHBORS) if NEIGHBORS else None
    
    r = random.random()
    cumulative = 0.0
    for next_hop, prob in probabilities.items():
        cumulative += prob
        if r <= cumulative:
            return next_hop
    return list(probabilities.keys())[-1]

def convert_to_dict(table):
    """Converte defaultdict em dicionário simples."""
    return {dest: dict(next_hops) for dest, next_hops in table.items()}

def send_hello():
    """Envia mensagens Hello para descobrir vizinhos ativos."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = {"type": "hello", "source": IP}
    while True:
        for neighbor in NEIGHBORS:
            try:
                sock.sendto(json.dumps(message).encode(), (neighbor, PORT))
                print(f"[{get_current_time()}] Enviado Hello para {neighbor}")
            except Exception as e:
                print(f"[{get_current_time()}] Erro ao enviar Hello para {neighbor}: {e}")
        time.sleep(HELLO_INTERVAL)

def send_update():
    """Envia mensagens de atualização com a tabela de feromônios."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = {"type": "update", "source": IP, "pheromones": convert_to_dict(pheromone_table)}
    while True:
        for neighbor in NEIGHBORS:
            try:
                sock.sendto(json.dumps(message).encode(), (neighbor, PORT))
                print(f"[{get_current_time()}] Enviado Update para {neighbor}")
            except Exception as e:
                print(f"[{get_current_time()}] Erro ao enviar Update para {neighbor}: {e}")
        time.sleep(UPDATE_INTERVAL)

def update_pheromones(received_table, source):
    """Atualiza a tabela de feromônios com base na tabela recebida."""
    try:
        for dest, next_hops in received_table.items():
            for next_hop, pheromone in next_hops.items():
                new_pheromone = (
                    (1 - EVAPORATION_RATE) * pheromone_table[dest].get(next_hop, PHEROMONE_INIT)
                    + EVAPORATION_RATE * pheromone
                )
                pheromone_table[dest][next_hop] = min(new_pheromone, 1000.0)  # Limite de 1000
        for dest in pheromone_table:
            if dest != IP:
                next_hop = choose_next_hop(dest)
                if next_hop:
                    latency = measure_latency(next_hop)
                    routing_table[dest] = {
                        "next_hop": next_hop,
                        "metric": latency,
                        "timestamp": time.time()
                    }
        print(f"[{get_current_time()}] Tabela de roteamento atualizada ({ROUTER_ID}): {dict(routing_table)}")
        print(f"[{get_current_time()}] Tabela de feromônios ({ROUTER_ID}): {convert_to_dict(pheromone_table)}")
    except Exception as e:
        print(f"[{get_current_time()}] Erro ao atualizar tabela de feromônios: {e}")

def receive_messages():
    """Recebe mensagens (Hello ou Update) e processa."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((IP, PORT))
        print(f"[{get_current_time()}] Escutando em {IP}:{PORT}")
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))  # Forçar UTF-8
                if message["type"] == "hello":
                    print(f"[{get_current_time()}] Recebido Hello de {message['source']}")
                    latency = measure_latency(message["source"])
                    pheromone_table[message["source"]][message["source"]] = min(
                        pheromone_table[message["source"]][message["source"]] + Q / latency, 1000.0
                    )
                elif message["type"] == "update":
                    print(f"[{get_current_time()}] Recebido Update de {message['source']}")
                    update_pheromones(message["pheromones"], message["source"])
            except Exception as e:
                print(f"[{get_current_time()}] Erro ao processar mensagem: {e}")
    except Exception as e:
        print(f"[{get_current_time()}] Erro ao iniciar socket: {e}")
        exit(1)

def main():
    """Função principal do roteador."""
    print(f"[{get_current_time()}] Iniciando roteador {ROUTER_ID} ({IP})")
    
    for neighbor in NEIGHBORS:
        pheromone_table[neighbor][neighbor] = PHEROMONE_INIT
    
    threading.Thread(target=send_hello, daemon=True).start()
    threading.Thread(target=send_update, daemon=True).start()
    threading.Thread(target=receive_messages, daemon=True).start()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            for dest in pheromone_table:
                for next_hop in pheromone_table[dest]:
                    pheromone_table[dest][next_hop] *= (1 - EVAPORATION_RATE)
            for dest, info in list(routing_table.items()):
                if dest != IP and time.time() - info["timestamp"] > CHECK_INTERVAL:
                    del routing_table[dest]
            print(f"[{get_current_time()}] Tabela de roteamento ({ROUTER_ID}): {dict(routing_table)}")
            print(f"[{get_current_time()}] Tabela de feromônios ({ROUTER_ID}): {convert_to_dict(pheromone_table)}")
        except Exception as e:
            print(f"[{get_current_time()}] Erro ao verificar tabela de roteamento: {e}")

if __name__ == "__main__":
    main()