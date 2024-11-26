from mlflow.tracking import MlflowClient

# Nom de l'expérience
experiment_name = "sklearn-20241126"  # Remplacez par le nom de l'expérience du jour

# Initialiser le client MLflow
client = MlflowClient()

# Récupérer l'expérience
experiment = client.get_experiment_by_name(experiment_name)

if experiment is None:
    print(f"No experiment found with name: {experiment_name}")
    experiment_name = "sklearn-20241126"
    new_experiment_id = client.create_experiment(experiment_name)
    print(f"Created new experiment with ID: {new_experiment_id}")
elif experiment.lifecycle_stage == "deleted":
    # Restaurer l'expérience si elle est supprimée
    client.restore_experiment(experiment.experiment_id)
    print(f"Experiment '{experiment_name}' has been restored.")
else:
    print(f"Experiment '{experiment_name}' is already active.")
