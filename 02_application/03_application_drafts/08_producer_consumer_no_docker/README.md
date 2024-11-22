# producer

* j'ai besoin de faire ma propre image Docker qui permet d'exécuter du code qui utilise des topics 
* J'arrive pas à utiliser celle de Jedha
* Comme le docker file de l'image de Jedha est pas dispo (merci les gars)
* Je repars de 0 et j'essaie de découvrir les lib à installer

```
File Explorer
Aller dans le répertoire cd .....fraud_detection_2\99_tooling\08_producer_no_docker
conda activate conda activate producer_nodocker
F5
Exception
./secrets.ps1 dans la console de Debug
F5
```
Ca tourne


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


# Pour le consumer
conda create --name consumer_nodocker --clone producer_nodocker
conda activate consumer_nodocker

Modification du code source du consumer pour lire topic_1 et faire faire une prédiction

conda install mlflow
conda install boto3 
conda install imbalanced-learn

    * mlflow est plutot GROS
    * Faudra s'assurer d'installer AWS sur l'image

Ajout de l'envoi de mails
    * Surtout pour vérifier si faut installer d'autres lib
    * https://myaccount.google.com/apppasswords
    * Ajout du dataframe en CSV en PJ




# TODO
* ~~Revoir load_MLflow_model~~
* ~~k_Experiments = "sklearn-20241027"~~
    * ~~Faut arriver à trouver la dernière expérimentation~~
    * ~~gerer les différents cas~~