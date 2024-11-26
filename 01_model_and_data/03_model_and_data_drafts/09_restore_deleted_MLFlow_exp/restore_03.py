import mlflow
from mlflow.tracking import MlflowClient

experiment_name = "sklearn-20241126"
client = MlflowClient()

# Vérifier l'expérience active
experiment = client.get_experiment_by_name(experiment_name)
if experiment:
    print(f"Found experiment: ID={experiment.experiment_id}, Stage={experiment.lifecycle_stage}")
else:
    print(f"No experiment found with name: {experiment_name}")
