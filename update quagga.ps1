# Construir a imagem Docker do Quagga
docker build -t quagga-router -f Dockerfile.quagga .

# Parar e remover os contêineres existentes
docker stop quagga1 quagga2 quagga3
docker rm quagga1 quagga2 quagga3

# Executar os contêineres Quagga com capacidades necessárias
docker run -d --name quagga1 --net drp-net --ip 172.20.0.5 `
  --cap-add=NET_ADMIN --cap-add=NET_RAW --cap-add=SYS_ADMIN `
  -v "$(Get-Location)\quagga_router1.conf:/etc/quagga/ripd.conf" `
  -v "$(Get-Location)\zebra_router1.conf:/etc/quagga/zebra.conf" `
  -v "$(Get-Location)\start-quagga.sh:/start-quagga.sh" `
  quagga-router

docker run -d --name quagga2 --net drp-net --ip 172.20.0.6 `
  --cap-add=NET_ADMIN --cap-add=NET_RAW --cap-add=SYS_ADMIN `
  -v "$(Get-Location)\quagga_router2.conf:/etc/quagga/ripd.conf" `
  -v "$(Get-Location)\zebra_router2.conf:/etc/quagga/zebra.conf" `
  -v "$(Get-Location)\start-quagga.sh:/start-quagga.sh" `
  quagga-router

docker run -d --name quagga3 --net drp-net --ip 172.20.0.7 `
  --cap-add=NET_ADMIN --cap-add=NET_RAW --cap-add=SYS_ADMIN `
  -v "$(Get-Location)\quagga_router3.conf:/etc/quagga/ripd.conf" `
  -v "$(Get-Location)\zebra_router3.conf:/etc/quagga/zebra.conf" `
  -v "$(Get-Location)\start-quagga.sh:/start-quagga.sh" `
  quagga-router
