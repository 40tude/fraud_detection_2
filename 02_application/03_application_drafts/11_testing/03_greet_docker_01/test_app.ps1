# test_app.ps1

. "./app/secrets.ps1"
docker-compose -f docker-compose-test.yml up -d
