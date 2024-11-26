from mlflow.tracking import MlflowClient

client = MlflowClient()

# Rechercher toutes les expériences
experiments = client.search_experiments()

for exp in experiments:
    print(f"ID={exp.experiment_id}, Name={exp.name}, Stage={exp.lifecycle_stage}")
