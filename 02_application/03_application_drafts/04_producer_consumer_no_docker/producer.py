#
# ! conda activate producer_nodocker
# ! Read the README.md

import time
import json
import requests
import ccloud_lib
import pandas as pd
from datetime import datetime, timezone
from confluent_kafka import Producer, Message

# Quand un message est produit avec une clé, Kafka utilise cette clé pour appliquer une fonction de hachage et déterminer la partition.
# Tous les messages avec la même clé sont envoyés dans la même partition, ce qui garantit leur ordre à l'intérieur de cette partition.
k_Key = "dummy"
k_Topic = "topic_1"
k_Client_Prop = "client.properties"
k_RT_Data_Producer = "https://real-time-payments-api.herokuapp.com/current-transactions"


def acked(err: int, msg: Message) -> None:
    global delivered_records
    # Delivery report handler called on successful or failed delivery of message
    if err is not None:
        print(f"Failed to deliver message: {err}", flush=True)
    else:
        delivered_records += 1
        print(
            f"Produced record to topic {msg.topic()} partition [{msg.partition()}] @ offset {msg.offset()}", flush=True
        )


def fetch_and_store() -> None:

    while True:
        try:
            response = requests.get(k_RT_Data_Producer)
            response.raise_for_status()  # Checks if the request was successful

            # convertit le contenu de la réponse (qui est au format JSON) en un objet Python (list, dico...)
            data = response.json()

            # vérifie si data est une chaîne de caractères
            # En fonction de la configuration de l'API
            # le contenu peut être renvoyé sous forme de chaîne JSON (texte brut) plutôt que directement sous forme de dictionnaire.
            # Si data est une chaîne, json.loads(data) convertit cette chaîne en un objet JSON Python (dictionnaire ou liste).
            if isinstance(data, str):
                data = json.loads(data)

            columns = data["columns"]
            index = data["index"]
            rows = data["data"]

            df = pd.DataFrame(data=rows, index=index, columns=columns)

            # ! 17 is hard coded
            # TODO : find a better way
            col = df["current_time"]
            df.insert(17, "unix_time", col)

            # convert to date string
            df.rename(columns={"current_time": "trans_date_trans_time"}, inplace=True)
            timestamp = df["trans_date_trans_time"].iloc[0]
            date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            str_date = date.strftime("%Y-%m-%d %H:%M:%S")

            df["trans_date_trans_time"] = df["trans_date_trans_time"].astype(str)
            df.at[index[0], "trans_date_trans_time"] = str_date

            # Modifies the order of columns in the df DataFrame
            # Moving the last column to the first position
            # Leaving all other columns in their original order
            cols = df.columns.tolist()
            reordered_cols = [cols[-1]] + cols[:-1]  # the last col then all the other until the before last col
            df = df[reordered_cols]

            data = {"columns": df.columns.tolist(), "index": df.index.tolist(), "data": df.values.tolist()}

            # Convertit le dictionnaire data en JSON et encode en UTF-8
            producer.produce(k_Topic, key=k_Key, value=json.dumps(data).encode("utf-8"), on_delivery=acked)
            print(f"Data sent:\n {data}\n\n", flush=True)
        except requests.RequestException as e:
            print(f"Request error: {e}", flush=True)
        except Exception as e:
            print(f"Unexpected error: {e}", flush=True)

        time.sleep(15)


if __name__ == "__main__":

    # Initialize configurations from "python.config" file
    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)

    # Create Producer instance
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)

    # %4|1730392410.023|CONFWARN|ccloud-python-client-9030d36c-0833-4218-9df6-e71c4030a986#producer-1| [thrd:app]: Configuration property session.timeout.ms is a consumer property and will be ignored by this producer instance
    # %6|1730392410.207|GETSUBSCRIPTIONS|ccloud-python-client-9030d36c-0833-4218-9df6-e71c4030a986#producer-1| [thrd:main]: Telemetry client instance id changed from AAAAAAAAAAAAAAAAAAAAAA to rXrhnKgeTlWDMIsp39NmPQ
    producer = Producer(producer_conf)

    # Create topic if it doesn't already exist
    # %4|1730392511.984|CONFWARN|ccloud-python-client-9030d36c-0833-4218-9df6-e71c4030a986#producer-2| [thrd:app]: Configuration property session.timeout.ms is a consumer property and will be ignored by this producer instance
    # %6|1730392512.084|GETSUBSCRIPTIONS|ccloud-python-client-9030d36c-0833-4218-9df6-e71c4030a986#producer-2| [thrd:main]: Telemetry client instance id changed from AAAAAAAAAAAAAAAAAAAAAA to v9QwCSOVTA2E/rsDguAVNQ
    # Pas utile car ici topic_1 existe déjà
    # ccloud_lib.create_topic(conf, k_Topic)

    fetch_and_store()
