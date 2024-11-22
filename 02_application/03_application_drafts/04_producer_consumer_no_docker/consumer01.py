#
# ! Read the README.md
# {"columns": ["trans_date_trans_time", "cc_num", "merchant", "category", "amt", "first", "last", "gender", "street", "city", "state", "zip", "lat", "long", "city_pop", "job", "dob", "trans_num", "unix_time", "merch_lat", "merch_long", "is_fraud"], "index": [75409], "data": [["2024-10-31 19:40:47", 4939976756738216, "fraud_Gerhold LLC", "home", 36.97, "Michelle", "Johnston", "F", "3531 Hamilton Highway", "Roma", "TX", 78584, 26.4215, -99.0025, 18128, "IT trainer", "1990-11-07", "f2d7e3f002a0d3ff996cd8b08b0f5cd7", 1730403647362, 26.288472, -99.055366, 0]]}

import ccloud_lib
from confluent_kafka import Consumer, KafkaException

k_Topic = "topic_1"
k_Client_Prop = "client.properties"


def get_and_print(consumer) -> None:
    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            print(f"Message reçu: {msg.value().decode('utf-8')}", flush=True)

    except KeyboardInterrupt:
        print("Lecture interrompue par l'utilisateur.", flush=True)

    finally:
        consumer.close()


if __name__ == "__main__":
    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)
    conf["group.id"] = "python-group-1"
    conf["auto.offset.reset"] = "earliest"

    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)

    # Créer un consommateur Kafka
    consumer = Consumer(consumer_conf)

    # S'abonner au topic
    consumer.subscribe([k_Topic])

    get_and_print(consumer)
