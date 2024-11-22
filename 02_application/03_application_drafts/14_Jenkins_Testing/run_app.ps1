# run_app.ps1

# . "./app/secrets.ps1"
# docker-compose up greet -d 

docker-compose --env-file ./app/.env up greet -d 
