from mlflow.tracking import MlflowClient

client = MlflowClient()
experiment_id = "34"

# Set the experiment back to active
client.restore_experiment(experiment_id)
print(f"Experiment {experiment_id} has been restored to active state.")
