FROM python:3.12-slim

WORKDIR /home/app

# To get access to the model stored on S3
RUN apt-get update
# nano
RUN apt-get install unzip        
RUN apt install curl -y

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
#####################

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

COPY app/ .




