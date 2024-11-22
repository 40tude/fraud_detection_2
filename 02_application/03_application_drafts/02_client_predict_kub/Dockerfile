# docker build -t client_predict .
# docker run -it --rm -v "$pwd/..:/home/app" client_predict
# docker run -d --mount source=Robert,target=/data --name my_container my_image

FROM continuumio/miniconda3
# FROM python:3.9-slim

WORKDIR /home/app

RUN apt-get update
RUN apt-get install nano unzip
RUN apt install curl -y

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

COPY requirements.txt /dependencies/requirements.txt
RUN pip install -r /dependencies/requirements.txt

COPY ./app/client_predict.py /home/app/
COPY ./app/for_predictions.csv /home/app/
CMD ["python", "/home/app/client_predict.py"]

