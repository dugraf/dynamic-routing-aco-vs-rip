# Projeto de Protocolo de Roteamento Dinâmico (DRP)

Este projeto implementa um protocolo de roteamento dinâmico personalizado baseado em **Otimização por Colônia de Formigas (ACO)** e compara seu desempenho com o **Routing Information Protocol (RIP)** implementado via Quagga. O projeto é executado em um ambiente baseado em Docker com uma topologia de três roteadores, utilizando uma interface web para monitoramento em tempo real das tabelas de roteamento, níveis de feromônios (para ACO) e eventos de rede.

A implementação atende aos requisitos de um trabalho acadêmico da disciplina "Redes de Computadores: Internetworking, Roteamento e Transmissão" da Unisinos (2025/2). Inclui um algoritmo de roteamento, implementação do protocolo, configuração da topologia e avaliação de desempenho.

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

```bash
drp_project/
│
├── app.py                     # Aplicação web Flask para monitoramento
├── config_router1.json        # Configuração do router1 (ACO)
├── config_router2.json        # Configuração do router2 (ACO)
├── config_router3.json        # Configuração do router3 (ACO)
├── Dockerfile                 # Dockerfile para os roteadores ACO
├── Dockerfile.quagga          # Dockerfile para os roteadores Quagga (RIP)
├── log_viewer.py              # Script para visualização de logs (não usado na execução principal)
├── quagga_router1.conf        # Configuração do RIP para quagga1
├── quagga_router2.conf        # Configuração do RIP para quagga2
├── quagga_router3.conf        # Configuração do RIP para quagga3
├── router.py                  # Implementação do protocolo de roteamento ACO
├── start-quagga.sh            # Script de inicialização dos daemons do Quagga
├── update.ps1                 # Script PowerShell para atualizar e executar roteadores ACO
├── update_quagga.ps1          # Script PowerShell para atualizar e executar roteadores Quagga
├── zebra_router1.conf         # Configuração do Zebra para quagga1
├── zebra_router2.conf         # Configuração do Zebra para quagga2
├── zebra_router3.conf         # Configuração do Zebra para quagga3
│
├── static/
│   └── style.css             # Estilos CSS para a interface web
│
└── templates/
    └── index.html            # Template HTML para a interface web
```

## Funcionalidades

- **Protocolo de Roteamento ACO**:
  - Implementa um algoritmo de roteamento inspirado em Otimização por Colônia de Formigas.
  - Utiliza tabelas de feromônios para seleção de caminhos com base em latência e probabilidade.
  - Troca mensagens `hello` e `update` via UDP (porta 5000).
  - Configurável via arquivos JSON (`config_routerX.json`).
- **RIP (Quagga)**:
  - Implementa o protocolo RIP usando o Quagga em contêineres Docker.
  - Configurado para uma topologia em malha completa com três roteadores.
- **Interface Web**:
  - Desenvolvida com Flask, exibe tabelas de roteamento, tabelas de feromônios (ACO) e contagem de eventos em tempo real.
  - Inclui gráficos para tipos de eventos e tamanhos das tabelas de roteamento.
- **Ambiente Docker**:
  - Executa seis roteadores (três para ACO, três para RIP) em uma rede Docker personalizada (`drp-net`, sub-rede 172.20.0.0/16).
  - Suporta configuração automatizada via scripts PowerShell.

## Pré-requisitos

- **Docker**: Instale o Docker Desktop (Windows/macOS) ou Docker (Linux).
- **Python 3.8+**: Necessário para executar a interface web (`app.py`).
- **PowerShell**: Para executar os scripts de automação (`update.ps1`, `update_quagga.ps1`).
- **Dependências**:
  - Pacotes Python: `flask`, `python-dateutil`.
  - Instale via:
    ```bash
    pip install flask python-dateutil
    ```

## Instruções de Configuração


### 1. Criar a Rede DockerCrie uma rede Docker personalizada para os roteadores:powershell
```bash
docker network create --subnet=172.20.0.0/16 drp-net
```

### 2. Configurar os Roteadores ACO
Os roteadores ACO são configurados pelos arquivos `config_router1.json`, `config_router2.json` e `config_router3.json`. Cada arquivo especifica o IP do roteador, seus vizinhos e parâmetros do protocolo.
Exemplo (`config_router1.json`):

```json
    {
        "ip": "172.20.0.2",
        "neighbors": ["172.20.0.3", "172.20.0.4"],
        "hello_interval": 2,
        "update_interval": 5,
        "check_interval": 15,
        "port": 5000
    }
```

### 3. Construir e Executar os Roteadores ACO
Use o script `update.ps1` para construir e executar os roteadores ACO:

```bash
.\update.ps1
```

### 4. Configurar os Roteadores Quagga (RIP)
Os roteadores RIP são configurados pelos arquivos `quagga_routerX.conf` (para o ripd) e `zebra_routerX.conf` (para o zebra).

### 5. Construir e Executar os Roteadores Quagga
Use o script `update_quagga.ps1` para construir e executar os roteadores Quagga.

### 6. Executar a Interface Web
A interface web monitora as tabelas de roteamento, tabelas de feromônios (ACO) e eventos de rede para os roteadores ACO e RIP.
```bash
python app.py
```
- Acesse a interface em http://localhost:5000.

### 7. Testar a Conectividade
Para testar o protocolo ACO, envie uma mensagem hello entre roteadores:

```bash
echo '{"type": "hello", "source": "172.20.0.2"}' | nc -u 172.20.0.3 5000
```

Para testar a conectividade do RIP:
```bash
docker exec -it quagga1 ping 172.20.0.6
docker exec -it quagga1 vtysh -c "show ip route"
```