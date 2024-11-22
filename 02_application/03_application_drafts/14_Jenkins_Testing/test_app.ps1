# test_app.ps1

# . "./app/secrets.ps1"
# docker-compose up greet_test -d 

docker-compose --env-file ./app/.env up greet_test -d