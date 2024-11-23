#
# ! conda activate producer_nodocker
# ./secrets.ps1
# session.timeout.ms=45000 commented in clients.properties

import time
import json
import requests
import ccloud_lib
import confluent_kafka
from confluent_kafka import Producer, Message
from msg_generator import get_message

# -----------------------------------------------------------------------------
k_Topic = "topic_3"
k_Key = "mock_resilient_topic"  # key for writing in topic_3
k_Client_Prop = "client.properties"
g_Delivered_Records = 0


# -----------------------------------------------------------------------------
# Delivery report handler called on successful or failed delivery of message
def on_produce(err: int, msg: Message) -> None:

    global g_Delivered_Records
    if err is not None:
        print(f"Failed to deliver message: {err}", flush=True)
    else:
        g_Delivered_Records += 1
        print(
            f"Produced record to topic {msg.topic()} partition [{msg.partition()}] @ offset {msg.offset()}", flush=True
        )


# -----------------------------------------------------------------------------
def fetch_and_store(producer) -> None:

    while True:
        try:
            response = get_message()
            data = json.loads(response) if isinstance(response, str) else response
            msg_id = data["id"]
            producer.produce(k_Topic, key=k_Key, value=json.dumps(data).encode("utf-8"), callback=on_produce)
            producer.flush()
            print(f"Msg with Id = {msg_id} sent", flush=True)
        except requests.RequestException as e:
            print(f"Request error: {e}", flush=True)
        except Exception as e:
            print(f"Unexpected error: {e}", flush=True)

        time.sleep(5)


# -----------------------------------------------------------------------------
def create_topic_producer() -> Producer:

    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)
    return producer


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Version de Kafka : {confluent_kafka.__version__}")
    producer = create_topic_producer()
    fetch_and_store(producer)
