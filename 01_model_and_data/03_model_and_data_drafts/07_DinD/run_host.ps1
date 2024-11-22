# run_host.ps1

docker run -it --rm --privileged `
    -v //var/run/docker.sock:/var/run/docker.sock `
    -v ${pwd}/hosted:/home/hosted `
    python-dind:3.12-slim