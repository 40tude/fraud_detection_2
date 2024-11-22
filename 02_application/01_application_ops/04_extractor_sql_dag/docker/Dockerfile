# Dockerfile

FROM python:3.12-slim

# Le répertoire de travail à l'intérieur du conteneur Docker
# defines the current working directory for all subsequent instructions in the 
# Dockerfile (RUN, COPY...), as well as for the execution of commands in the resulting container
WORKDIR /home/app

# requirements.txt will be in /home/app/requirements.txt (not a big deal)
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

# copy the content of /app from the host to the current directory (WORKDIR) 
COPY app/ .




