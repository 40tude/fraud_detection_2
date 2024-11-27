#
# ! Virtual Env consumer_no_docker
# J'avais un problème avec la version 7 du modèle qui balancait toujours FRAUD, FRAUD, FRAUD, FRAUD, FRAUD...
# Je pense finalement que tout était OK que c'est juste qu'ils ont, à 2 ou 3 jours de la soutenance, fait varié le % de fraudes

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
k_DATA_PRODUCER = "https://real-time-payments-api.herokuapp.com/current-transactions"


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

    model = None

    try:
        boto3.setup_default_session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
    except NoCredentialsError:
        print("Please make sure to run `./secrets.ps1` before to run this script.")
        return None  # Exit early if credentials are missing

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
def test_PAS_BIEN() -> None:

    # ! Ne leve PAS d'exception même si AWS_ACCESS_KEY_ID n'est pas définie
    # On peut enlever le bloc try except il sert à rien ici
    # MlflowClient n'interagit avec les artefacts ou les backends (comme S3) qu'au moment où une action spécifique est demandée
    # Exemple, list_artifacts).
    # Si les credentials AWS sont absents ou incorrects, c'est à ce moment-là que ça part en vrille

    try:
        boto3.setup_default_session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
    except NoCredentialsError:
        print("Please make sure to run `./secrets.ps1` before to run this script.")
        return None  # Exit early if credentials are missing

    mlflow.set_tracking_uri(k_MLflow_Tracking_URL)
    client = MlflowClient()
    # ! Part en vrille si AWS_ACCESS_KEY_ID n'est pas définie
    artifacts = client.list_artifacts("225ce244bfc94287b1c70d24f73b6842")
    # print(f"Artifacts in run 225ce244bfc94287b1c70d24f73b6842: {[artifact.path for artifact in artifacts]}")


# -----------------------------------------------------------------------------
def test_MIEUX() -> None:
    def check_aws_env_vars() -> None:
        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required AWS environment variables: {', '.join(missing_vars)}")

    try:
        check_aws_env_vars()
        boto3.setup_default_session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        # Validate credentials with a test call
        boto3.client("sts").get_caller_identity()
    except EnvironmentError as env_err:
        print(env_err)
        return None  # Exit early if environment variables are missing
    except Exception as e:
        print(f"Error with AWS credentials: {e}")
        return None

    # Continue with MLflow interaction
    mlflow.set_tracking_uri(k_MLflow_Tracking_URL)
    client = MlflowClient()
    artifacts = client.list_artifacts("225ce244bfc94287b1c70d24f73b6842")
    # print(f"Artifacts in run 225ce244bfc94287b1c70d24f73b6842: {[artifact.path for artifact in artifacts]}")


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
def from_url(model_to_use: Fraud_Model) -> None:

    model_columns = expected_columns(model_to_use)

    print(f"\n\n----------------------------------------")
    print(f"From {k_DATA_PRODUCER}")
    for i in range(10):
        to_predict_df = get_one_transaction()
        print("Colonnes des données de production :")
        print(f"{to_predict_df.columns.tolist()}")

        to_predict_df = to_predict_df[model_columns]
        print("Colonnes des données envoyées au modèle :")
        print(f"{to_predict_df.columns.tolist()}")

        input_df = pd.DataFrame([to_predict_df.iloc[0]])
        print(f"{input_df}")

        prediction = model_to_use.loaded_model.predict(input_df)
        if prediction:
            prediction = "Fraud"
        else:
            prediction = "Not Fraud"
        print(f"Prediction : {prediction}\n")
        # time.sleep(10)
    return


# -----------------------------------------------------------------------------
def compare_model_predictions(v1: int, v2: int) -> None:

    m1 = get_model_in_version(v1)
    if not m1:
        raise ValueError("No suitable model in v1")

    m2 = get_model_in_version(v2)
    if not m2:
        raise ValueError("No suitable model in v2")

    model_columns = expected_columns(m1)
    # print(f"{model_columns}")

    for i in range(10):
        to_predict_df = get_one_transaction()
        # print(f"{to_predict_df}")
        to_predict_df = to_predict_df[model_columns]
        input_df = pd.DataFrame([to_predict_df.iloc[0]])
        # print(f"{to_predict_df}")

        prediction1 = m1.loaded_model.predict(input_df)
        prediction1 = ["Fraud" if pred else "Not Fraud" for pred in prediction1]
        prediction2 = m2.loaded_model.predict(input_df)
        prediction2 = ["Fraud" if pred else "Not Fraud" for pred in prediction2]
        print(f"{prediction1} - {prediction2}")

    return


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    os.chdir(Path(__file__).parent)

    # test_PAS_BIEN()  # à tester quand AWS_ACCESS_KEY_ID est pas définie
    test_MIEUX()

    # model_to_use = get_model_in_version(k_Model_Version)
    # if not model_to_use:
    #     raise ValueError("No suitable model found")

    # from_local(model_to_use)
    # from_url(model_to_use)

    print(f"[V{k_Model_Version1}]          - [V{k_Model_Version2}]")
    compare_model_predictions(k_Model_Version1, k_Model_Version2)
