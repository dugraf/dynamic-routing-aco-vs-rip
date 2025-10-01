from flask import Flask, render_template, jsonify
import subprocess
import time
import re
from datetime import datetime
import pytz

app = Flask(__name__)

# Configurar fuso horário
TIMEZONE = pytz.timezone('America/Sao_Paulo')

def get_docker_logs(container_name):
    """Obtém os logs de um contêiner Docker."""
    try:
        result = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True,
            text=True,
            encoding='utf-8',  # Forçar UTF-8
            check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        return [f"Erro ao obter logs de {container_name}: {e}"]

def parse_logs(logs, router_id):
    """Analisa os logs e extrai eventos, tabelas de roteamento e feromônios."""
    events = []
    routing_table = {}
    pheromone_table = {}
    event_counts = {"hello": 0, "update": 0, "error": 0, "table": 0}
    
    for line in logs:
        timestamp_match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
        timestamp = timestamp_match.group(1) if timestamp_match else "Unknown"
        
        event_class = "info"
        if "Recebido Hello" in line:
            event_class = "hello"
            event_counts["hello"] += 1
        elif "Recebido Update" in line:
            event_class = "update"
            event_counts["update"] += 1
        elif "Erro" in line or "inf" in line:
            event_class = "error"
            event_counts["error"] += 1
        elif "Tabela de roteamento atualizada" in line:
            event_class = "table"
            event_counts["table"] += 1
            try:
                table_str = line.split(": ", 1)[1]
                routing_table = eval(table_str)
            except Exception as e:
                print(f"[{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}] Erro ao parsear tabela de roteamento em {router_id}: {e}")
        elif "Tabela de feromônios" in line:
            try:
                table_str = line.split(": ", 1)[1]
                pheromone_table = eval(table_str)
            except Exception as e:
                print(f"[{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}] Erro ao parsear tabela de feromônios em {router_id}: {e}")
        
        events.append({
            "timestamp": timestamp,
            "router_id": router_id,
            "message": line,
            "class": event_class
        })
    
    return events, routing_table, pheromone_table, event_counts

def format_routing_table(routing_table):
    """Formata a tabela de roteamento para JSON."""
    rows = []
    for dest, info in routing_table.items():
        rows.append({
            "destination": dest,
            "next_hop": info.get("next_hop", "N/A"),
            "metric": info.get("metric", "N/A"),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("timestamp", 0)))
        })
    return rows

def format_pheromone_table(pheromone_table):
    """Formata a tabela de feromônios para JSON."""
    rows = []
    for dest, next_hops in pheromone_table.items():
        for next_hop, pheromone in next_hops.items():
            rows.append({
                "destination": dest,
                "next_hop": next_hop,
                "pheromone": round(pheromone, 2)
            })
    return rows

@app.route('/')
def index():
    """Renderiza a página principal."""
    return render_template('index.html')

@app.route('/api/logs')
def get_logs():
    """Retorna os logs, tabelas de roteamento, feromônios e contagem de eventos."""
    containers = ["router1", "router2", "router3"]
    all_events = []
    routing_tables = {}
    pheromone_tables = {}
    event_counts = {}
    
    for container in containers:
        logs = get_docker_logs(container)
        events, routing_table, pheromone_table, counts = parse_logs(logs, container)
        all_events.extend(events[-10:])
        routing_tables[container] = format_routing_table(routing_table)
        pheromone_tables[container] = format_pheromone_table(pheromone_table)
        event_counts[container] = counts
        print(f"[{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}] {container} - Rotas: {routing_tables[container]}")
        print(f"[{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}] {container} - Feromônios: {pheromone_tables[container]}")
    
    return jsonify({
        "events": sorted(all_events, key=lambda x: x["timestamp"], reverse=True)[:30],
        "routing_tables": routing_tables,
        "pheromone_tables": pheromone_tables,
        "event_counts": event_counts,
        "last_updated": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)