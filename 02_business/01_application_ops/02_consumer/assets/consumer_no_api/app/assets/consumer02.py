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
k_Key = "Zoubida"  # key for writing in topic_2
k_Latest = 1  # latest model version used to make prediction
k_Before_Last = 0  # before last model version used to make prediction
k_Topic_1 = "topic_1"  # topics  Id
k_Topic_2 = "topic_2"
k_GroupId = "python-group-2"  # default = python-group-2. Group used to read from topic_1
k_Experiments = "sklearn-20241027"  # ! FIXME :
k_Client_Prop = "client.properties"
k_mail_to = "philippe.baucour@gmail.com"
k_MLflow_Tracking_URL = "https://fraud-detection-2-ab95815c7127.herokuapp.com/"

g_Delivered_Records = 0


# -----------------------------------------------------------------------------
def send_mail(df):

    # Configuration du serveur SMTP et des informations de connexion
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Création de l'objet message
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = "philippe.baucour@gmail.com"
    msg["Subject"] = "Security alert - Fraud detected"

    # Création du corps du message
    body = "15H63 - Ceci est un message texte d'une ligne."
    msg.attach(MIMEText(body, "plain"))

    # Conversion du DataFrame en fichier CSV en mémoire
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Ajout du CSV comme pièce jointe
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(csv_buffer.read())
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f"attachment; filename=fraud_detection_report.csv")
    msg.attach(attachment)

    # Connexion au serveur SMTP et envoi du email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Sécurise la connexion
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, k_mail_to, msg.as_string())
        print("E-mail successfully sent.")
    except Exception as e:
        print(f"Error sending e-mail : \n{e}")
    return


# -----------------------------------------------------------------------------
def get_one_transaction_from_topic_1(consumer):
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
                print(f"Erreur de format JSON : {e}")
                continue

    except KeyboardInterrupt:
        print("CTRL+C detected. Closing gently.", flush=True)

    finally:
        consumer.close()


# -----------------------------------------------------------------------------
def get_latest_model(client, model_name, version=1):

    runs = client.search_runs(
        experiment_ids=[client.get_experiment_by_name(model_name).experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["start_time DESC"],
    )

    if version == 1:
        return runs[0] if runs else None  # lest version
    elif version == 0:
        return runs[1] if len(runs) > 1 else None  # before last version if it exists

    return None  # Invalid version


# -----------------------------------------------------------------------------
def create_topic_consumer():

    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)

    # définit l'ID du groupe de consommateurs auquel appartient le consommateur
    conf["group.id"] = k_GroupId

    # le consommateur commence la lecture au début si aucun offset n’a été enregistré pour lui ou reprend là où il s’est arrêté.
    # ! L'offset pour chaque partition est stocké au niveau du groupe et non du consommateur individuel
    # Donc un consommateur rejoignant le même groupe reprendra là où le dernier en était
    # Si jamais on change le nom du groupe (python-group-42) alors l'utilisateur va lire le plus ancien des messages (earliest)
    conf["auto.offset.reset"] = "earliest"

    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    consumer = Consumer(consumer_conf)
    consumer.subscribe([k_Topic_1])
    return consumer


# -----------------------------------------------------------------------------
def create_MLflow_client(consumer):

    try:
        boto3.setup_default_session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
    except NoCredentialsError:
        print("Please make sure to run `./secrets.ps1` before to run this script.", flush=True)

    mlflow.set_tracking_uri(k_MLflow_Tracking_URL)

    # Create an MLflow client
    client = MlflowClient()
    return client


# -----------------------------------------------------------------------------
def load_model(client, version):
    # Get the lastest model available
    latest_run = get_latest_model(client, k_Experiments, version)
    if not latest_run:
        raise ValueError("No suitable model found")

    # Get the URI of the model
    model_uri = f"runs:/{latest_run.info.run_id}/model"
    print(f"URI of the best model : {model_uri}", flush=True)

    loaded_model = mlflow.sklearn.load_model(model_uri)
    return loaded_model


# -----------------------------------------------------------------------------
# If called twice, do not transfer the model again
def load_MLflow_model(client, version=k_Latest):

    if not hasattr(load_MLflow_model, "Model_Version_Set") or load_MLflow_model.Model_Version_Set != version:
        load_MLflow_model.Model_Version_Set = version
        load_MLflow_model.CachedModel = load_model(client, version)
    return load_MLflow_model.CachedModel


# -----------------------------------------------------------------------------
def make_prediction(loaded_model, to_predict_df):
    # Ne garde que les colonnes attendues pour faire tourner le modèle (vire entre autres et bien évidement la colonne is_fraud)
    # C'est pour ça que même si dans topic_1 il n'y a pas de colonne_1 (celle qui contenait un indice dans le jeu d'entrainement) ce n'est pas un problème
    # En effet, lors de l'entrainement on supprime cette colonne qui ne contient pas d'information pour la prédiction
    # Voir la fonction load_data(self) dans 02_train_code\02_sklearn\01_template\train.py par exemple
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
if __name__ == "__main__":
    # for testing send_one_mail() function calls
    # df = pd.DataFrame({"Name": ["Tom", "nick", "krish", "jack"], "Age": [20, 21, 19, 18]})
    # send_one_mail(df)

    consumer = create_topic_consumer()

    try:
        current_transaction = get_one_transaction_from_topic_1(consumer)
        to_predict_df = current_transaction.copy()
        print(to_predict_df)
    except KafkaException as e:
        print(f"Erreur Kafka : {e}", flush=True)

    client = create_MLflow_client(consumer)
    loaded_model = load_MLflow_model(client, k_Latest)
    prediction = make_prediction(loaded_model, to_predict_df)

    # current_transaction is only 1 line
    # overwrite current is_fraud feature with model inference
    current_transaction.loc[current_transaction.index[0], "is_fraud"] = prediction

    if prediction:
        prediction_str = "Fraud"
        send_mail(current_transaction)
    else:
        prediction_str = "Not Fraud"

    print(f"Prediction : {prediction_str}", flush=True)

    # TODO : Add a feature "fraud_confirmed" to the 1 line dataframe "current_transaction" and save it topic_2
    current_transaction = current_transaction.assign(fraud_confirmed=[np.nan])

    print("Current transaction to be sent to topic_2", flush=True)
    print(current_transaction, flush=True)
    print()

    # store current_transaction in topic_2
    # Weird to read the conf file twice. No?
    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)
    data_as_json = current_transaction.to_json(orient="records")
    producer.produce(k_Topic_2, key=k_Key, value=data_as_json.encode("utf-8"), on_delivery=acked)
    producer.flush()
    time.sleep(5)

    print("Consumer is done", flush=True)
