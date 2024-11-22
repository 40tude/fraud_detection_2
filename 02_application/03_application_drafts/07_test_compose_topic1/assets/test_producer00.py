# Code inspired from Confluent Cloud official examples library
# https://github.com/confluentinc/examples/blob/7.1.1-post/clients/cloud/python/producer.py

from confluent_kafka import Producer
import json
import ccloud_lib  # Library not installed with pip but imported from ccloud_lib.py
import numpy as np
import time

# Initialize configurations from "python.config" file
CONF = ccloud_lib.read_ccloud_config("client.properties")
TOPIC = "topic_1"

# Create Producer instance
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(CONF)
producer = Producer(producer_conf)

# Create topic if it doesn't already exist
ccloud_lib.create_topic(CONF, TOPIC)


delivered_records = 0


# Callback called acked (triggered by poll() or flush())
# when a message has been successfully delivered or
# permanently failed delivery (after retries).
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


try:
    while True:
        record_key = "weather"
        record_value = json.dumps({"degrees_in_celsion": np.random.randint(10, 40)})
        print("Producing record: {}\t{}".format(record_key, record_value))

        # This will actually send data to your topic
        producer.produce(TOPIC, key=record_key, value=record_value, on_delivery=acked)
        # p.poll() serves delivery reports (on_delivery)
        # from previous produce() calls thanks to acked callback
        producer.poll(0)
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    producer.flush()  # Finish producing the latest event before stopping the whole script
