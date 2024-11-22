* j'ai besoin de faire ma propre image Docker qui permet d'exécuter du code qui utilise des topics 
* J'arrive pas à utiliser celle de Jedha
* Comme le docker file de l'image de Jedha est pas dispo (merci les gars)
* Je repars de 0 et j'essaie de découvrir les lib à installer

<!-- conda install pandas -c conda-forge -y
conda install requests
conda install librdkafka -c conda-forge -->

```bash
conda install requests pandas librdkafka -c conda-forge -y
pip install confluent_kafka  avro-python3
```


```bash
pip list --format=freeze >> ./requirements.txt
```



docker-compose up 
On voir Hello à l'écran


docker-compose up -d
docker-compose logs app1
Pour voir Hello dans les logs


docker-compose logs app1
docker-compose logs app1

docker-compose ps

docker-compose down
docker-compose stop
docker-compose stop app1
