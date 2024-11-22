FROM python:3.12-slim

WORKDIR /home/app

# Specific to the consumer
# To get access to the model stored on S3
RUN apt-get update
RUN apt-get install nano unzip
RUN apt install curl -y

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
#####################

RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip curl librdkafka-dev && \
    rm -rf /var/lib/apt/lists/* 

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

COPY app/ .

