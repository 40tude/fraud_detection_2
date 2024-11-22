FROM python:3.12-slim

WORKDIR /home/app

# RUN apt-get update

# RUN apt-get update && \
#     apt-get install -y --no-install-recommends unzip curl librdkafka-dev && \
#     rm -rf /var/lib/apt/lists/* 

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

COPY app/ .




