#
# ! Virtual Env consumer_no_docker
# J'avais un problème avec la version 7 du modèle qui balancait toujours FRAUD, FRAUD, FRAUD, FRAUD, FRAUD...
# J'ai un doute
# J'ai récupéer hiersoir des transaction en live
# Je veux faire fcontionner Version 4 et Version 7 sur ces transactions ainsi que sur le fraud_dataset et voir qui a raison
# Si je trouve rien faudra comparer le dataset "historique" (30 jours) avec le dataset courant

import os
import json

# import time
import boto3
import mlflow
import requests
import pandas as pd

from pathlib import Path
from datetime import datetime, timezone
from mlflow.tracking import MlflowClient
from botocore.exceptions import NoCredentialsError

k_Model_Version1 = 4
k_Model_Version2 = 7
k_model_name = "random_forest"
k_MLflow_Tracking_URL = "https://fraud-detection-2-ab95815c7127.herokuapp.com/"
# k_DATA_PRODUCER = "https://real-time-payments-api.herokuapp.com/current-transactions"

k_Data_Dir = Path("../../04_data")
k_Prod_Data_Dir = Path("./data")
k_Fraud_Test_csv = "fraud_test.csv"
k_Production_csv = "production.csv"


# -----------------------------------------------------------------------------
def get_one_transaction() -> pd.DataFrame:

    response = requests.get(k_DATA_PRODUCER)
    data = response.json()

    if isinstance(data, str):
        data = json.loads(data)

    columns = data["columns"]
    index = data["index"]
    rows = data["data"]

    df = pd.DataFrame(data=rows, index=index, columns=columns)
    # ['cc_num', 'merchant', 'category', 'amt', 'first', 'last', 'gender', 'street', 'city', 'state', 'zip', 'lat', 'long', 'city_pop', 'job', 'dob', 'trans_num', 'merch_lat', 'merch_long', 'is_fraud', 'current_time']
    # print(f"{df.columns.tolist()}")

    # ! DANGER - 17 is hard coded
    col = df["current_time"]
    df.insert(17, "unix_time", col)
    # ['cc_num', 'merchant', 'category', 'amt', 'first', 'last', 'gender', 'street', 'city', 'state', 'zip', 'lat', 'long', 'city_pop', 'job', 'dob', 'trans_num', 'unix_time', 'merch_lat', 'merch_long', 'is_fraud', 'current_time']
    # print(f"{df.columns.tolist()}")

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
    # ['trans_date_trans_time', 'cc_num', 'merchant', 'category', 'amt', 'first', 'last', 'gender', 'street', 'city', 'state', 'zip', 'lat', 'long', 'city_pop', 'job', 'dob', 'trans_num', 'unix_time', 'merch_lat', 'merch_long', 'is_fraud']
    # print(f"{df.columns.tolist()}")

    return df


# -----------------------------------------------------------------------------
class Fraud_Model:
    def __init__(self, client: MlflowClient, version: int) -> None:
        self.name = k_model_name
        self.client = client
        self.version = version
        self.version_info = client.get_model_version(name=self.name, version=self.version)
        self.uri = f"runs:/{self.version_info.run_id}/model"

        # print(f"Attempting to load model from URI: {self.uri}")
        self.loaded_model = mlflow.sklearn.load_model(self.uri)


# -----------------------------------------------------------------------------
def get_model_in_version(version_n: int) -> Fraud_Model | None:

    def check_aws_env_vars() -> None:
        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required AWS environment variables: {', '.join(missing_vars)}")

    model = None

    try:
        check_aws_env_vars()
        boto3.setup_default_session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        # STS = Security Token Service
        # Validate credentials with a test call
        boto3.client("sts").get_caller_identity()
    except EnvironmentError as env_err:
        print(env_err)
        return None  # Exit early if environment variables are missing
    except Exception as e:
        print(f"Mmake sure to run `./secrets.ps1` before to run this script : {e}")
        return None

    # Set MLflow tracking URI
    mlflow.set_tracking_uri(k_MLflow_Tracking_URL)
    client = MlflowClient()

    # Search for all model versions
    model_versions = client.search_model_versions(f"name='{k_model_name}'")

    # Check if the requested version exists
    for model_version in model_versions:
        if int(model_version.version) == version_n:
            try:
                model = Fraud_Model(client, version_n)
                return model
            except Exception as e:
                print(f"Error loading model version {version_n}: {e}")
                return None

    print(f"Model version {version_n} not found.")
    return None


# -----------------------------------------------------------------------------
# Ne garde que les colonnes attendues pour faire tourner le modèle (vire entre autres et bien évidement la colonne is_fraud)
# C'est pour ça que même si dans topic_1 il n'y a pas de colonne_1 (celle qui contenait un indice dans le jeu d'entrainement) ce n'est pas un problème
# En effet, lors de l'entrainement on supprime cette colonne qui ne contient pas d'information pour la prédiction
def expected_columns(model_to_use: Fraud_Model) -> list[str]:

    model_columns: list[str] = (
        model_to_use.loaded_model.feature_names_in_ if hasattr(model_to_use.loaded_model, "feature_names_in_") else []
    )
    # print("Colonnes attendues par le modèle :", model_columns)
    return model_columns


# -----------------------------------------------------------------------------
# Charge un extrait du jeu de données. Les 10 premières lignes sont légales. Les 10 dernieres sont des fraudes
def from_local(model_to_use: Fraud_Model) -> None:

    model_columns = expected_columns(model_to_use)

    to_predict_df = pd.read_csv("./for_predictions.csv", delimiter=";")
    print("Colonnes des données du dataset de train :")
    print(f"{to_predict_df.columns.tolist()}")

    to_predict_df = to_predict_df[model_columns]
    print("Colonnes des données envoyées au modèle :")
    print(f"{to_predict_df.columns.tolist()}")

    print(f"\n\n----------------------------------------")
    print(f"From local .csv file : ")
    for i in range(len(to_predict_df)):
        input_df = pd.DataFrame([to_predict_df.iloc[i]])
        print(f"{input_df}")

        prediction = model_to_use.loaded_model.predict(input_df)
        if prediction:
            prediction = "Fraud"
        else:
            prediction = "Not Fraud"
        print(f"Prediction : {prediction}\n")
    return


# -----------------------------------------------------------------------------
def compare_model_predictions(v1: int, v2: int) -> None:

    m1 = get_model_in_version(v1)
    if not m1:
        raise ValueError("No suitable model in v1")

    m2 = get_model_in_version(v2)
    if not m2:
        raise ValueError("No suitable model in v2")

    # We assert expected_columns are the same
    # TODO : DONE - They are the same : ['cc_num' 'amt' 'zip' 'lat' 'long' 'city_pop' 'unix_time' 'merch_lat'  'merch_long']
    model_columns = expected_columns(m2)
    # print(f"{model_columns}")
    # model_columns = expected_columns(m1)
    # print(f"{model_columns}")

    # PRODUCTION dataset
    production_df = pd.read_csv(k_Prod_Data_Dir / k_Production_csv)
    production_df = production_df[model_columns]

    print(f"\n\n------------------------------")
    print(f"[V{k_Model_Version1}]          - [V{k_Model_Version2}]")
    for i in range(50):
        input_df = pd.DataFrame([production_df.loc[i]])
        prediction1 = m1.loaded_model.predict(input_df)
        prediction1 = ["Fraud" if pred else "Not Fraud" for pred in prediction1]
        prediction2 = m2.loaded_model.predict(input_df)
        prediction2 = ["Fraud" if pred else "Not Fraud" for pred in prediction2]
        print(f"{prediction1} - {prediction2}")

    # TRAINING dataset
    training_df = pd.read_csv(k_Data_Dir / k_Fraud_Test_csv)
    training_df = training_df[training_df["is_fraud"] == True]
    training_df = training_df.reset_index(drop=True)
    training_df = training_df[model_columns]

    print(f"\n\n------------------------------")
    print(f"[V{k_Model_Version1}]          - [V{k_Model_Version2}]")
    for i in range(50):
        input_df = pd.DataFrame([training_df.loc[i]])
        prediction1 = m1.loaded_model.predict(input_df)
        prediction1 = ["Fraud" if pred else "Not Fraud" for pred in prediction1]
        prediction2 = m2.loaded_model.predict(input_df)
        prediction2 = ["Fraud" if pred else "Not Fraud" for pred in prediction2]
        print(f"{prediction1} - {prediction2}")

    return


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    os.chdir(Path(__file__).parent)

    compare_model_predictions(k_Model_Version1, k_Model_Version2)
