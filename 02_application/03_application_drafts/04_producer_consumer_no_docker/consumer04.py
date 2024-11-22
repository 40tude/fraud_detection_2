#
# ! conda activate consumer_nodocker

import os
import json
import time
import boto3
import mlflow
import ccloud_lib
import numpy as np
import pandas as pd
from io import StringIO
from typing import Optional
from mlflow.tracking import MlflowClient
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
k_Latest = 1  # latest model version used to make prediction
k_Before_Last = 0  # before last model version used to make prediction
k_Topic_1 = "topic_1"  # topics  Id
k_Topic_2 = "topic_2"
k_GroupId = "python-group-2"  # default = python-group-2. Group used to read from topic_1
k_Client_Prop = "client.properties"
k_MLflow_Tracking_URL = "https://fraud-detection-2-ab95815c7127.herokuapp.com/"

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

    # finally:
    #     consumer.close()

    return None


# -----------------------------------------------------------------------------
# ! PAY ATTENTION
# ! This function is tricky because of the different cases to be dealt with
def get_run(client, version=k_Latest):

    # Get the Ids of the last two experiements (if available)
    def get_2latest_experiments(client):

        experiments = client.search_experiments(order_by=["creation_time DESC"])

        if len(experiments) > 1:
            return experiments[0], experiments[1]  # last + before last
        elif experiments:
            return experiments[0], None  # Last + None
        else:
            return None, None  # None + None

    # Get the run according version (k_Latest or k_Before_Last)
    def get_run_from_experiment(experiment):
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="attributes.status = 'FINISHED'",
            order_by=["start_time DESC"],
        )
        if version == k_Latest:
            return runs[0] if runs else None  # last version if it exists
        elif version == k_Before_Last:
            return runs[1] if len(runs) > 1 else None  # before last version if it exists
        return None  # no run available

    # Get the last 2 experiments
    latest_experiment, previous_experiment = get_2latest_experiments(client)

    if not latest_experiment:
        print("No experiments found", flush=True)
        return None

    # Il y a un latest_experiment
    # Tente d'y récupérer le run demandé (voir le paramètre version qui vaut k_Latest ou k_Before_Last)
    run = get_run_from_experiment(latest_experiment)
    if run:
        return run

    # If the version of the requested run could not be found in latest_experiment
    # Consider the case where you request the Before_Last (penultimate?) version of a run in an experiment that contains only one run.
    # In this case, you need to search for Latest run in the penultimate experiment.
    if previous_experiment and version == k_Before_Last:
        version = k_Latest
        return get_run_from_experiment(previous_experiment)

    return None  # No run available


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
# def create_MLflow_client(consumer):
def create_MLflow_client():

    try:
        boto3.setup_default_session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
    except NoCredentialsError:
        print("Please make sure to run `./secrets.ps1` before to run this script.", flush=True)

    mlflow.set_tracking_uri(k_MLflow_Tracking_URL)

    client = MlflowClient()
    return client


# -----------------------------------------------------------------------------
# Get the lastest model available
def load_model(client, version=k_Latest):

    latest_run = get_run(client, version)
    if not latest_run:
        raise ValueError("No suitable model found")

    # Get the URI of the model
    model_uri = f"runs:/{latest_run.info.run_id}/model"
    print(f"URI of the best model : {model_uri}", flush=True)

    loaded_model = mlflow.sklearn.load_model(model_uri)
    return loaded_model


# -----------------------------------------------------------------------------
# If called twice, do not transfer the model again
# I try to anticipate the fact that the code will be in a never ending loop at one point
def load_MLflow_model(client, version=k_Latest):

    if not hasattr(load_MLflow_model, "Model_Version_Set") or load_MLflow_model.Model_Version_Set != version:
        load_MLflow_model.Model_Version_Set = version
        load_MLflow_model.CachedModel = load_model(client, version)
    return load_MLflow_model.CachedModel


# -----------------------------------------------------------------------------
def make_prediction(loaded_model, to_predict_df):

    # Keep only the columns needed to run the model (the is_fraud feature is excluded)
    # That's why even if topic_1 doesn't have a column_1 (the one that contained an index in the training set), it's not a problem.
    # In fact, during training we delete this column, which contains no usefull information for inferences.
    # See the load_data(self) function in 02_train_code\02_sklearn\01_template\train.py for example.

    model_columns = loaded_model.feature_names_in_ if hasattr(loaded_model, "feature_names_in_") else []
    # print("Colonnes attendues par le modèle :", model_columns, flush=True)
    to_predict_df = to_predict_df[model_columns]

    # prediction is an np array
    # Here there is 1 and only 1 prediction
    prediction = loaded_model.predict(to_predict_df)

    return prediction[0]


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
    time.sleep(5)  # if the code right after write_transaction_to_topic_2 this helps make sure acked is called


# -----------------------------------------------------------------------------
# def afficher_types_colonnes(dataframe: pd.DataFrame) -> None:
#     for colonne, dtype in dataframe.dtypes.items():
#         print(f"Colonne '{colonne}': {dtype}")


# -----------------------------------------------------------------------------
def read_infere_store(consumer, producer) -> None:

    # client = create_MLflow_client(consumer)
    client = create_MLflow_client()

    while True:
        try:
            current_transaction_df = read_transaction_from_topic_1(consumer)
            to_predict_df = current_transaction_df.copy()
            # print(to_predict_df,flush=True)

            loaded_model = load_MLflow_model(client, k_Latest)
            prediction = make_prediction(loaded_model, to_predict_df)

            # current_transaction is only 1 line
            # overwrite current is_fraud feature with model inference
            current_transaction_df.loc[current_transaction_df.index[0], "is_fraud"] = prediction

            if prediction:
                prediction_str = "Fraud"
                send_mail(current_transaction_df)
            else:
                prediction_str = "Not Fraud"
                # send_mail(current_transaction) # testing purpose

            print(f"Prediction : {prediction_str}", flush=True)

            write_transaction_to_topic_2(producer, current_transaction_df)

        except KafkaException as e:
            print(f"Kafka error : {e}", flush=True)

        time.sleep(15)


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # consumer reads from topic_1
    # producer writes on topic_2
    consumer = create_topic_consumer()
    producer = create_topic_producer()
    read_infere_store(consumer, producer)


# testing purpose
# df = pd.DataFrame({"Name": ["Tom", "nick", "krish", "jack"], "Age": [20, 21, 19, 18]})
# send_one_mail(df)
