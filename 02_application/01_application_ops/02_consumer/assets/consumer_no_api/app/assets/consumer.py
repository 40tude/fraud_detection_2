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

            print(f"Received Message: {msg.value().decode('utf-8')}", flush=True)

    except KeyboardInterrupt:
        print("User interrupt (CTRL+C). Gently closing.", flush=True)

    finally:
        consumer.close()


if __name__ == "__main__":
    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)
    conf["group.id"] = "python-group-1"
    conf["auto.offset.reset"] = "earliest"

    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    consumer = Consumer(consumer_conf)
    consumer.subscribe([k_Topic])
    get_and_print(consumer)
