#
# ! conda activate consumer_nodocker
# Read from topic1
# use API to get predictions (modelizer must be running. \99_tooling\14_modelizer_no_docker)
# Write to topic2

import requests  # to talk to modelizer via API
import os
import json
import time

import ccloud_lib
import numpy as np
import pandas as pd
from io import StringIO
from typing import Optional

from confluent_kafka import Consumer, KafkaException
from confluent_kafka import Producer, Message

# Pour les mails
import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


# -----------------------------------------------------------------------------
k_Key = "fraud_detection_2"  # key for writing in topic_2
k_Topic_1 = "topic_1"  # topics  Id
k_Topic_2 = "topic_2"
k_GroupId = "python-group-2"  # default = python-group-2. Group used to read from topic_1
k_Client_Prop = "client.properties"
g_Delivered_Records = 0  # ! global variable. Be careful


# -----------------------------------------------------------------------------
def send_mail(df):

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    email_recipient = os.getenv("EMAIL_RECIPIENT")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = email_recipient
    msg["Subject"] = "Security alert - Fraud detected"

    body = "A potentially fraudulent transaction has been detected. Please review the attached document."
    msg.attach(MIMEText(body, "plain"))

    # Convert dataframe to csv in memory
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # attach the csv to the mail
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(csv_buffer.read())
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f"attachment; filename=fraud_detection_report.csv")
    msg.attach(attachment)

    # Connect and send
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # protect the connexion
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, email_recipient, msg.as_string())
        print("E-mail successfully sent.", flush=True)
    except Exception as e:
        print(f"Error sending e-mail. Did you run ./secrets.ps1 ? : \n{e}", flush=True)
    return


# -----------------------------------------------------------------------------
def create_topic_consumer() -> Consumer:

    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)

    # defines the ID of the consumer group to which the consumer belongs
    conf["group.id"] = k_GroupId

    # the consumer starts reading at the beginning if no offset has been recorded for him or continue to read from where he left off.
    # ! The offset for each partition is stored at group level, NOT at individual consumer level.
    # So a consumer joining the same group will pick up where the last one left off
    # If you change the group name (python-group-42), the user will read the earliest message.
    conf["auto.offset.reset"] = "earliest"

    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    consumer = Consumer(consumer_conf)
    consumer.subscribe([k_Topic_1])
    return consumer


# -----------------------------------------------------------------------------
def create_topic_producer():

    # Weird to read the conf file twice. No? See create_topic_consumer()
    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)
    return producer


# -----------------------------------------------------------------------------
def read_transaction_from_topic_1(consumer: Consumer) -> Optional[pd.DataFrame]:  # Union[pd.DataFrame, None]:
    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            json_str = msg.value().decode("utf-8")
            print(f"Message reçu: {json_str}\n\n", flush=True)

            try:
                json_dict = json.loads(json_str)
                df = pd.DataFrame(data=json_dict["data"], columns=json_dict["columns"], index=json_dict["index"])
                return df
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error in JSON format : {e}", flush=True)
                continue

    except KeyboardInterrupt:
        print("CTRL+C detected. Closing gently.", flush=True)
        consumer.close()

    return None


# -----------------------------------------------------------------------------
# Callback used when writing on topic_2
def acked(err: int, msg: Message) -> None:

    global g_Delivered_Records

    # Delivery report handler called on successful or failed delivery of message
    if err is not None:
        print(f"Failed to deliver message: {err}", flush=True)
    else:
        g_Delivered_Records += 1
        print(
            f"Produced record to topic {msg.topic()} partition [{msg.partition()}] @ offset {msg.offset()}", flush=True
        )


# -----------------------------------------------------------------------------
def write_transaction_to_topic_2(producer, current_transaction):
    # Add a feature "fraud_confirmed" to the 1 line dataframe "current_transaction" and save it topic_2
    current_transaction = current_transaction.assign(fraud_confirmed=[np.nan])

    print("Current transaction to be sent to topic_2", flush=True)
    print(current_transaction, flush=True)
    print(flush=True)

    data_as_json = current_transaction.to_json(orient="records")
    producer.produce(k_Topic_2, key=k_Key, value=data_as_json.encode("utf-8"), on_delivery=acked)
    producer.flush()
    # time.sleep(5)  # if the code right after write_transaction_to_topic_2 this helps make sure acked is called


# -----------------------------------------------------------------------------
def read_infere_store(consumer, producer) -> None:

    port = os.getenv("PORT")
    Modelizer_URL = f"http://modelizer:{port}/predict"
    # Modelizer_URL = "http://127.0.0.1:8000/predict"

    while True:
        try:
            current_transaction_df = read_transaction_from_topic_1(consumer)

            json_str = current_transaction_df.to_json(orient="split")
            json_data = json.loads(json_str)

            response = requests.post(Modelizer_URL, json=json_data)
            if response.status_code == 200:
                response_dict = response.json()
                prediction = int(response_dict.get("prediction"))
                current_transaction_df.loc[current_transaction_df.index[0], "is_fraud"] = prediction
                if prediction:
                    send_mail(current_transaction_df)
                # Add a feature "fraud_confirmed", set it to Nan and write in topic_2
                write_transaction_to_topic_2(producer, current_transaction_df)

            else:
                print("Échec :", response.status_code, response.text)

        except KafkaException as e:
            print(f"Kafka error: {e}", flush=True)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}", flush=True)

        except json.JSONDecodeError as e:
            print(f"JSON error: {e}", flush=True)

        # except Exception as e:
        #     print(f"Unexpected error: {e}", flush=True)

        time.sleep(15)


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # consumer reads from topic_1
    # producer writes on topic_2
    consumer = create_topic_consumer()
    producer = create_topic_producer()
    read_infere_store(consumer, producer)


# -----------------------------------------------------------------------------
# One day... Let's check if modelizer API server is up and running before to go further
# Modelizer may take 15-30 sec on first launch because getting the models take time
# import time
# import requests

# def is_api_ready(url, retries=10, delay=3):
#     for i in range(retries):
#         try:
#             response = requests.get(url)
#             if response.status_code == 200:
#                 return True
#         except requests.exceptions.RequestException:
#             pass
#         print(f"Attempt {i+1}/{retries} failed, retrying in {delay} seconds...")
#         time.sleep(delay)
#     return False

# api_url = "http://modelizer:8000/predict"
# if is_api_ready(api_url):
#     print("API is ready, starting consumer logic.")
#     # Lancer la logique du client ici
# else:
#     print("API is not available after several attempts.")
