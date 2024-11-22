# clean_greet

docker ps -a -q --filter "name=logger_sql*" | ForEach-Object { docker rm $_ }
docker image ls --format "{{.Repository}}:{{.ID}}" | Select-String "^logger_sql" | ForEach-Object { $id = ($_ -replace '.*:', ''); docker rmi -f $id }
