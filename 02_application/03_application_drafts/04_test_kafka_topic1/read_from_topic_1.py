# va lire dans topic_1 les transactions qui reste
# l'affichage est brute de fonderie
# Y a pas de traitement

from confluent_kafka import Consumer
import json
import ccloud_lib
import time

k_Topic = "topic_1"


if __name__ == "__main__":
    conf = ccloud_lib.read_ccloud_config("python.config")

    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    consumer_conf["group.id"] = "my_weather_consumer"
    consumer_conf["auto.offset.reset"] = (
        "earliest"  # This means that you will consume latest messages that your script haven't consumed yet!
    )
    consumer = Consumer(consumer_conf)
    consumer.subscribe([k_Topic])

    try:
        while True:
            msg = consumer.poll(1.0)  # Search for all non-consumed events. It times out after 1 second
            if msg is None:
                print("Waiting for message or event/error in poll()")
                continue
            elif msg.error():
                print("error: {}".format(msg.error()))
            else:
                record_key = msg.key()
                record_value = msg.value()
                data = json.loads(record_value)
                print(data)
                print(msg.offset())
                time.sleep(2.0)  # Wait n sec
        pass
    finally:
        consumer.close()
