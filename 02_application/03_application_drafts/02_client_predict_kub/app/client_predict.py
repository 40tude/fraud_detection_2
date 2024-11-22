import os
import mlflow
import boto3

# import mlflow.pyfunc
import pandas as pd
from pathlib import Path
from mlflow.tracking import MlflowClient


import json
import requests

# import pandas as pd
from datetime import datetime, timezone


# Pour les mails
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart


# Constants
k_MLflow_Tracking_URL = "https://fraud-202406-70e02a9739f2.herokuapp.com/"
k_Experiments = "template-sklearn-20240630"
k_DATA_PRODUCER = "https://real-time-payments-api.herokuapp.com/current-transactions"


# -----------------------------------------------------------------------------
def get_one_transaction():

    response = requests.get(k_DATA_PRODUCER)
    data = response.json()

    if isinstance(data, str):
        data = json.loads(data)

    columns = data["columns"]
    index = data["index"]
    rows = data["data"]

    df = pd.DataFrame(data=rows, index=index, columns=columns)

    pd.set_option("display.max_columns", None)
    # display(df)

    # ! DANGER - 17 is hard coded
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
    return df


# -----------------------------------------------------------------------------
# Je le met là pour l'instant ça peut servir un jour
# Voir qu'on recoit un df avec uniquement les 9 paramètres numériques utilisés pour les prédictions
# Y a moyen de faire mieux
def send_one_mail(df):

    # # Configuration du serveur SMTP et des informations de connexion
    # smtp_server = 'smtp.gmail.com'
    # smtp_port = 587
    # smtp_user = 'xxxx.yyyy@gmail.com'
    # smtp_password = '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'

    # # Création de l'objet message
    # msg = MIMEMultipart()
    # msg['From'] = smtp_user
    # msg['To'] = 'martine.baucour@gmail.com'
    # msg['Subject'] = 'ALARM - Fraud detected'

    # # Création du corps du message
    # body = '15H33 - Ceci est un message texte d\'une ligne.'
    # msg.attach(MIMEText(body, 'plain'))

    # # Connexion au serveur SMTP et envoi de l'email
    # try:
    #     with smtplib.SMTP(smtp_server, smtp_port) as server:
    #         server.starttls()  # Sécurise la connexion
    #         server.login(smtp_user, smtp_password)
    #         server.sendmail(smtp_user, 'martine.baucour@gmail.com', msg.as_string())
    #     print("E-mail envoyé avec succès.")
    # except Exception as e:
    #     print(f"Erreur lors de l'envoi de l'e-mail : {e}")

    print("Un mail envoyé : ")
    print(df)
    print()
    return


# -----------------------------------------------------------------------------
# Search for the best model according the speed criteria (get inspired)
def get_best_model(client, model_name):
    best_run = None
    best_total_run_time = +float("inf")

    runs = client.search_runs(
        experiment_ids=[client.get_experiment_by_name(model_name).experiment_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["start_time DESC"],
    )

    for run in runs:
        if "total_run_time" in run.data.metrics and run.data.metrics["total_run_time"] < best_total_run_time:
            best_run = run
            best_total_run_time = run.data.metrics["total_run_time"]

    return best_run


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # current_file = Path(__file__).resolve()
    # current_directory = current_file.parent
    # os.chdir(current_directory)
    # # Charge un extrait du jeu de données. Les 10 premières lignes sont légales. Les 10 dernieres sont des fraudes
    # to_predict_df = pd.read_csv("./for_predictions.csv", delimiter=";")
    # # print("Colonnes des données de train initiales :", to_predict_df.columns.tolist())

    to_predict_df = get_one_transaction()

    try:
        boto3.setup_default_session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
    except NoCredentialsError:
        print("Please make sure to run `./secrets.ps1` before to run this script.")

    mlflow.set_tracking_uri(k_MLflow_Tracking_URL)

    # Create an MLflow client
    client = MlflowClient()

    # Get the best model run
    best_run = get_best_model(client, k_Experiments)
    if not best_run:
        raise ValueError("No suitable model found")

    # Get the model URI for the best run
    model_uri = f"runs:/{best_run.info.run_id}/model"
    print(f"URI of the best model : {model_uri}")

    # Load the best model
    loaded_model = mlflow.sklearn.load_model(model_uri)

    # Ne garde que les colonnes attendues pour faire tourner le modèle (vire aussi la colonne is_fraud)
    model_columns = loaded_model.feature_names_in_ if hasattr(loaded_model, "feature_names_in_") else []
    # print("Colonnes attendues par le modèle :", model_columns)
    to_predict_df = to_predict_df[model_columns]

    for i in range(len(to_predict_df)):
        input_df = pd.DataFrame([to_predict_df.iloc[i]])
        prediction = loaded_model.predict(input_df)
        if prediction:
            prediction = "Fraud"
            send_one_mail(input_df)
        else:
            prediction = "Not Fraud"
        print(f"Prediction : {prediction}")
