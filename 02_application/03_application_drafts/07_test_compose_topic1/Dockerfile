FROM jedha/confluent-image
WORKDIR /home/app
COPY . /home/app

# Lancer le service Confluent, attendre, puis exécuter le script Python
CMD ["/bin/bash", "-c", "/etc/confluent/docker/run & sleep 5 && python test_producer02.py"]
