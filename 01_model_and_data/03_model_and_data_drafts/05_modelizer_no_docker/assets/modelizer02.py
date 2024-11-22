import os
# import json
import uvicorn
import mlflow
import boto3
import pandas as pd

from pydantic import BaseModel
from typing import List, Union
from fastapi import FastAPI, HTTPException                #, Request
from fastapi.responses import HTMLResponse
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
def get_models():
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

    return latest, previous

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
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
latest_mod, previous_mod = get_models()

for m in [latest_mod, previous_mod]:        
    print("Version          :", m.version)                                               
    print("Source Run ID    :", m.version_info.run_id)                                   
    print("URI              :", m.uri)

current_mod = latest_mod

app = FastAPI()

class InputData(BaseModel):
    columns: List[str]
    index: List[int]
    data: List[List[Union[str, int, float]]]  







# -----------------------------------------------------------------------------
@app.post("/predict")
async def predict(data: InputData):
    try:
        df = pd.DataFrame(data=data.data, columns=data.columns, index=data.index)
        # print(df)
        # prediction = make_prediction(loaded_model, df)
        prediction = make_prediction(current_mod.loaded_model, df)
        # print (prediction)
        return {"prediction": f"{prediction}"}

    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail="Check that the number of parameters and their spelling are correct.",
        )








# -----------------------------------------------------------------------------
@app.get("/docs")
async def get_docs():
    return {"docs_url": "/docs"}


# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
        <html>
            <head>
                <title>Modelizer</title>
            </head>
            <body>
                <h1>Welcome to Fraud Detection 2 Modelizer</h1>
                <ul>
                    <li>Use the endpoint <code>/predict</code> to make predictions</li>
                    <li>Use the endpoint <code>/docs</code> to test the API<br />
                        <ul>    
                            <li>Once the "/predict" panel is oen, click the "Try it out" button</li> 
                            <li>For a first test, copy'n paste the line below (from "{" to "}", both included)</li>
                            <li>This is not a fraudulent transaction, the prediction will be 0
                            <div> 
                            <code>
{
    "columns": ["trans_date_trans_time", "cc_num", "merchant", "category", "amt", "first", "last", "gender", "street", "city", "state", "zip", "lat", "long", "city_pop", "job", "dob", "trans_num", "unix_time", "merch_lat", "merch_long", "is_fraud"],
    "index": [164481],
    "data": [["2024-10-31 15:58:29", 38530489946071, "fraud_Cole, Hills and Jewess", "home", 22.9, "Laura", "Johns", "F", "95835 Garcia Rue", "Arcadia", "SC", 29320, 34.9572, -81.9916, 530, "Animal technologist", "1989-05-14", "fd6f5d5606f49ffbc33c2a28dfe006f1", 1730390309560, 34.831131, -82.885952, 0]]
}
                            </code></div></li>

                            

                            <li>For a second test, copy'n paste the line below.</li>
                            <li>This is a fraudulent transaction, the prediction will be 1
                            <div> 
                            <code>


{
    "columns": ["trans_date_trans_time", "cc_num", "merchant", "category", "amt", "first", "last", "gender", "street", "city", "state", "zip", "lat", "long", "city_pop", "job", "dob", "trans_num", "unix_time", "merch_lat", "merch_long", "is_fraud"],
    "index": [1781],
    "data": [["2020-06-21 22:37", 6564459919350820, "fraud_Nienow PLC", "entertainment", 620.33, "Douglas", "Willis", "M", "619 Jeremy Garden Apt. 681", "Benton", "WI", 53803, 42.5545, -90.3508, 1306, "Public relations officer", "1958-09-10", "47a9987ae81d99f7832a54b29a77bf4b", 1371854247, 42.771834, -90.158365, 1]]
}
                            </code></div></li>


                        </ul>
                    </li>
                </ul>
                <p>&nbsp;</p>

            </body>
        </html>
    """
    return html_content


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # either set ``port`` to the value of the environment variable PORT or use 8000 (de facto the default value)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)







# # -----------------------------------------------------------------------------
# k_Latest = 1  # latest model version used to make prediction
# k_Before_Last = 0  # before last model version used to make prediction
# k_MLflow_Tracking_URL = "https://fraud-detection-2-ab95815c7127.herokuapp.com/"

# # -----------------------------------------------------------------------------
# # ! PAY ATTENTION
# # ! This function is tricky because of the different cases to be dealt with
# def get_run(client, version=k_Latest):

#     # Get the Ids of the last two experiements (if available)
#     def get_2latest_experiments(client):

#         experiments = client.search_experiments(order_by=["creation_time DESC"])

#         if len(experiments) > 1:
#             return experiments[0], experiments[1]  # last + before last
#         elif experiments:
#             return experiments[0], None  # Last + None
#         else:
#             return None, None  # None + None

#     # Get the run according version (k_Latest or k_Before_Last)
#     def get_run_from_experiment(experiment):
#         runs = client.search_runs(
#             experiment_ids=[experiment.experiment_id],
#             filter_string="attributes.status = 'FINISHED'",
#             order_by=["start_time DESC"],
#         )
#         if version == k_Latest:
#             return runs[0] if runs else None  # last version if it exists
#         elif version == k_Before_Last:
#             return runs[1] if len(runs) > 1 else None  # before last version if it exists
#         return None  # no run available

#     # Get the last 2 experiments
#     latest_experiment, previous_experiment = get_2latest_experiments(client)

#     if not latest_experiment:
#         print("No experiments found", flush=True)
#         return None

#     # Il y a un latest_experiment
#     # Tente d'y récupérer le run demandé (voir le paramètre version qui vaut k_Latest ou k_Before_Last)
#     run = get_run_from_experiment(latest_experiment)
#     if run:
#         return run

#     # If the version of the requested run could not be found in latest_experiment
#     # Consider the case where you request the Before_Last (penultimate?) version of a run in an experiment that contains only one run.
#     # In this case, you need to search for Latest run in the penultimate experiment.
#     if previous_experiment and version == k_Before_Last:
#         version = k_Latest
#         return get_run_from_experiment(previous_experiment)

#     return None  # No run available


# # -----------------------------------------------------------------------------
# # Get the lastest model available
# def load_model(client, version=k_Latest):

#     latest_run = get_run(client, version)
#     if not latest_run:
#         raise ValueError("No suitable model found")

#     # Get the URI of the model
#     model_uri = f"runs:/{latest_run.info.run_id}/model"
#     print(f"URI of latest model : {model_uri}", flush=True)

#     loaded_model = mlflow.sklearn.load_model(model_uri)
#     return loaded_model

# # -----------------------------------------------------------------------------
# # If called twice, do not transfer the model again
# # I try to anticipate the fact that the code will be in a never ending loop at one point
# def load_MLflow_model(client, version=k_Latest):

#     if not hasattr(load_MLflow_model, "Model_Version_Set") or load_MLflow_model.Model_Version_Set != version:
#         load_MLflow_model.Model_Version_Set = version
#         load_MLflow_model.CachedModel = load_model(client, version)
#     return load_MLflow_model.CachedModel


# # -----------------------------------------------------------------------------
# def create_MLflow_client():

#     try:
#         boto3.setup_default_session(
#             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#             region_name=os.getenv("AWS_REGION"),
#         )
#     except NoCredentialsError:
#         print("Please make sure to run `./secrets.ps1` before to run this script.", flush=True)

#     mlflow.set_tracking_uri(k_MLflow_Tracking_URL)

#     client = MlflowClient()
#     return client








# # -----------------------------------------------------------------------------
# client = create_MLflow_client()
# loaded_model = load_MLflow_model(client, k_Latest)
