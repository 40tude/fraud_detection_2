import os
import boto3
import mlflow
from mlflow.tracking import MlflowClient

# -----------------------------------------------------------------------------
k_MLflow_Tracking_URL = "https://fraud-detection-2-ab95815c7127.herokuapp.com/"
k_model_name = "random_forest"

# -----------------------------------------------------------------------------
class Fraud_Model:
    def __init__(self, client, version):
        self.name = k_model_name
        self.client=client
        self.version= version
        self.version_info = client.get_model_version(name=self.name, version=self.version)

        self.uri = f"runs:/{self.version_info.run_id}/model"
        self.loaded_model = mlflow.sklearn.load_model(self.uri)

# -----------------------------------------------------------------------------
if __name__ == "__main__":

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

    model_versions = client.search_model_versions(f"name='{k_model_name}'")
    model_versions = sorted(model_versions, key=lambda x: int(x.version), reverse=True)

    latest = Fraud_Model(client, model_versions[0].version) if model_versions[0].version else None
    previous = Fraud_Model(client, model_versions[1].version) if model_versions[1].version else None

    for m in [latest, previous]:        
        print("Version          :", m.version)                                               
        print("Source Run ID    :", m.version_info.run_id)                                   
        print("URI              :", m.uri)