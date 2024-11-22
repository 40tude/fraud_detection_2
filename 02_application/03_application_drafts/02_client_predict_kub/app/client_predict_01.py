# Se rappeler que qu'on faisait les prédictions en utilisant QUE les numériques 

import os
import mlflow
import pandas as pd
from pathlib import Path

k_MLflow_Tracking_URL = "https://fraud-202406-70e02a9739f2.herokuapp.com/"
k_Logged_Model = "runs:/1fcd6f0ced3b491fa67f67f4d16f8712/model"

if __name__ == "__main__":

    current_file = Path(__file__).resolve()
    current_directory = current_file.parent
    os.chdir(current_directory)
    # Charge un extrait du jeu de données. Les 10 premières lignes sont légales. Les 10 dernieres sont des fraudes
    to_predict_df = pd.read_csv("./for_predictions.csv", delimiter=";")
    # print("Colonnes des données de train initiales :", to_predict_df.columns.tolist())

    mlflow.set_tracking_uri(k_MLflow_Tracking_URL)
    loaded_model = mlflow.sklearn.load_model(k_Logged_Model)
    
    # Ne garde que les colonnes attendues pour faire tourner le modèle (vire aussi la colonne is_fraud)
    model_columns = loaded_model.feature_names_in_ if hasattr(loaded_model, 'feature_names_in_') else []
    # print("Colonnes attendues par le modèle :", model_columns)
    to_predict_df = to_predict_df[model_columns]

    for i in range (len(to_predict_df)):
        input_df = pd.DataFrame([to_predict_df.iloc[i]])
        prediction = loaded_model.predict(input_df)
        prediction = "Fraud" if prediction else "Not Fraud"
        print(f"Prediction : {prediction}")
