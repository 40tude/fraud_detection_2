#Dockerfile

FROM python:3.12-slim
ARG REQUIREMENTS_FILE

WORKDIR /home

RUN apt-get update

COPY docker/${REQUIREMENTS_FILE} .
RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE}    

COPY app/ ./app
COPY tests/ ./tests