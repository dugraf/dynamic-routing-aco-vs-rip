# Compilar a imagem Docker
docker build -t drp-router .

# Parar os containers existentes
docker stop router1 router2 router3

# Remover os containers existentes
docker rm router1 router2 router3

# Rodar os containers com as configurações específicas
docker run -d --name router3 --net drp-net --ip 172.20.0.4 -v ${PWD}/config_router3.json:/app/config.json drp-router
docker run -d --name router2 --net drp-net --ip 172.20.0.3 -v ${PWD}/config_router2.json:/app/config.json drp-router
docker run -d --name router1 --net drp-net --ip 172.20.0.2 -v ${PWD}/config_router1.json:/app/config.json drp-router