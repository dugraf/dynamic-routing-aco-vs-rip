import subprocess
import time
import os
from tabulate import tabulate
from colorama import init, Fore, Style
import re
from datetime import datetime

# Inicializar colorama para cores no terminal (Windows)
init()

def get_docker_logs(container_name):
    """Obtém os logs de um contêiner Docker."""
    try:
        result = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        return [f"Erro ao obter logs de {container_name}: {e}"]

def parse_logs(logs, router_id):
    """Analisa os logs e extrai eventos importantes."""
    events = []
    routing_table = {}
    for line in logs:
        # Adicionar timestamp ao evento
        timestamp_match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
        timestamp = timestamp_match.group(1) if timestamp_match else "Unknown"
        
        # Colorir eventos
        if "Recebido Hello" in line:
            events.append(f"{Fore.GREEN}{timestamp} {router_id}: {line}{Style.RESET_ALL}")
        elif "Recebido Update" in line:
            events.append(f"{Fore.CYAN}{timestamp} {router_id}: {line}{Style.RESET_ALL}")
        elif "Erro" in line:
            events.append(f"{Fore.RED}{timestamp} {router_id}: {line}{Style.RESET_ALL}")
        elif "Tabela de roteamento atualizada" in line:
            events.append(f"{Fore.YELLOW}{timestamp} {router_id}: {line}{Style.RESET_ALL}")
            # Extrair tabela de roteamento
            try:
                table_str = line.split(": ", 1)[1]
                routing_table = eval(table_str)  # Converter string para dicionário
            except:
                routing_table = {}
        else:
            events.append(f"{timestamp} {router_id}: {line}")
    return events, routing_table

def format_routing_table(routing_table, router_id):
    """Formata a tabela de roteamento em uma tabela visual."""
    headers = ["Destino", "Próximo Salto", "Métrica", "Timestamp"]
    rows = []
    for dest, info in routing_table.items():
        rows.append([
            dest,
            info.get("next_hop", "N/A"),
            info.get("metric", "N/A"),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("timestamp", 0)))
        ])
    return f"\nTabela de Roteamento ({router_id}):\n{tabulate(rows, headers, tablefmt='grid')}"

def display_logs():
    """Exibe os logs dos contêineres em uma interface amigável."""
    containers = ["router1", "router2", "router3"]
    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Limpar tela (Windows/Linux)
        print(f"{Fore.BLUE}=== Monitor de Logs DRP (Atualizado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ==={Style.RESET_ALL}\n")
        
        all_events = []
        for container in containers:
            logs = get_docker_logs(container)
            events, routing_table = parse_logs(logs, container)
            all_events.extend(events[-10:])  # Mostrar apenas os últimos 10 eventos por roteador
            print(format_routing_table(routing_table, container))
        
        print("\nEventos Recentes:")
        for event in sorted(all_events[-30:], reverse=True):  # Mostrar os últimos 30 eventos
            print(event)
        
        time.sleep(2)  # Atualizar a cada 2 segundos

if __name__ == "__main__":
    try:
        display_logs()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Monitor encerrado pelo usuário.{Style.RESET_ALL}")