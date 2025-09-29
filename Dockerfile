FROM ubuntu:20.04

# Definir variável de ambiente para evitar interação durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Atualizar e instalar pacotes
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iperf \
    net-tools \
    quagga \
    tzdata \
    nmap \
    traceroute \
    iftop \
    iputils-ping \
    tcpdump \
    wireshark \
    iperf3 \
    curl \
    wget \
    dnsutils \
    netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instalar a biblioteca Python 'pandas'
RUN pip3 install pandas pytz

# Configurar fuso horário para America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && echo "America/Sao_Paulo" > /etc/timezone
ENV TZ=America/Sao_Paulo

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos do contexto para o container
COPY . /app

# Comando para rodar o script Python
CMD ["python3", "router.py"]
