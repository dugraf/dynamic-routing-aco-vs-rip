#!/bin/bash
echo "Iniciando Quagga..."
# Iniciar zebra
/usr/sbin/zebra -d -f /etc/quagga/zebra.conf
if [ $? -ne 0 ]; then
    echo "Erro ao iniciar zebra"
    exit 1
fi
echo "Zebra iniciado com sucesso"

# Iniciar ripd
/usr/sbin/ripd -d -f /etc/quagga/ripd.conf
if [ $? -ne 0 ]; then
    echo "Erro ao iniciar ripd"
    exit 1
fi
echo "RIPd iniciado com sucesso"

# Manter o contêiner ativo e monitorar logs
tail -f /var/log/quagga/ripd.log