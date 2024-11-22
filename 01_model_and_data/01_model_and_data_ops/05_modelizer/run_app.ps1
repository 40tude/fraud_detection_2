# . "./app/secrets.ps1"
# docker-compose up -d

# run a specific service from docker-compose.yml + clean up the container at the end
# Since there is only one this is weird to pass the name of the service
# Nod -d beacause I want to see the logs
# docker compose run --rm modelizer     # NOT a good idea does not take into account network port in docker-compose
docker-compose up                       # docker container prune -f if you want to clean
