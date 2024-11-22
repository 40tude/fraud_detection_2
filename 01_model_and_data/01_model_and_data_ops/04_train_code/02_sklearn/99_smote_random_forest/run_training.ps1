. "./secrets.ps1"

mlflow run --experiment-name $env:MLFLOW_EXPERIMENT_NAME .
# If you want to pass parameters which will overwrite the ones defined in MLproject use this line
# mlflow run --experiment-name $env:MLFLOW_EXPERIMENT_NAME -P n_estimators=10 . 