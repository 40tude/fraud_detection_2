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
