* Faut avoir un cluster sur confluent (https://confluent.cloud/home) et créer un ``python.config`` (voir le cours)
* Sous VSCode
* Ouvrir un terminal dans ``99_tooling\04_test_kafka_topic1``
* Lancer   : ``./run_confluent_image``
* Sous bash lancer : python write_to_topic_1.py

* Ouvrir un autre terminal
* Lancer   : ``./run_confluent_image``
* Sous bash lancer : ``python read_from_topic_1.py``
* Faut imaginer que ``python read_from_topic_1.py`` remette les données en forme et fasse faire une prédiction dessus (doit pas être dur à coder)


### Note
* Plutôt que de lancer 2 terminaux on peut imaginer de lancer les code en tâche de fond dans l'image confluent 
* On doit même être capable de scripter tout ça  histoire que tout soit automatisé et qu'on ai plus à s'en occuper
