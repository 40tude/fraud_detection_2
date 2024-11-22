FROM python:3.12-slim

WORKDIR /home/app

RUN apt-get update

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

COPY app/ .




