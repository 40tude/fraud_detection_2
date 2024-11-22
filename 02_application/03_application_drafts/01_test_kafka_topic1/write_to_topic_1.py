# toutes les 20 secondes
# va chercher une transaction simulée
# l'ecrit dans topic_1
#
import time
import requests

# from kafka import KafkaProducer
from confluent_kafka import Producer
import ccloud_lib  # Library not installed with pip but imported from ccloud_lib.py

# Configuration du producteur Kafka
# producer = KafkaProducer(bootstrap_servers="localhost:9092")

k_Topic = "topic_1"


def acked(err, msg):
    global delivered_records
    # Delivery report handler called on successful or failed delivery of message
    if err is not None:
        print("Failed to deliver message: {}".format(err))
    else:
        delivered_records += 1
        print(
            "Produced record to topic {} partition [{}] @ offset {}".format(msg.topic(), msg.partition(), msg.offset())
        )


def fetch_and_store():
    url = "https://real-time-payments-api.herokuapp.com/current-transactions"
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Vérifie si la requête a réussi
            data = response.json()
            # producer.send("transactions_topic", value=data.encode("utf-8"))
            producer.produce(k_Topic, key="dummy", value=data.encode("utf-8"), on_delivery=acked)
            print(f"Données envoyées: {data}")
        except requests.RequestException as e:
            print(f"Erreur lors de la requête: {e}")
        except Exception as e:
            print(f"Erreur inattendue: {e}")

        time.sleep(15)


if __name__ == "__main__":

    # Initialize configurations from "python.config" file
    conf = ccloud_lib.read_ccloud_config("python.config")

    # Create Producer instance
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)

    # Create topic if it doesn't already exist
    ccloud_lib.create_topic(conf, k_Topic)

    fetch_and_store()
