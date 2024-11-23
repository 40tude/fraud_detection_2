import pandas as pd
import os
from sqlalchemy import create_engine, types

k_table_name = "fraud_detection_2_table"

DATABASE_URL = os.getenv("LOGGER_SQL_URI")
engine = create_engine(DATABASE_URL)


# -----------------------------------------------------------------------------
def get_sqlalchemy_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return types.Integer
    elif pd.api.types.is_float_dtype(dtype):
        return types.Float
    elif pd.api.types.is_string_dtype(dtype):
        return types.String
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return types.DateTime
    else:
        raise ValueError(f"Type non supporté : {dtype}")


# -----------------------------------------------------------------------------
def create_table_from_dataframe(df, table_name):
    column_types = {col: get_sqlalchemy_type(dtype) for col, dtype in df.dtypes.items()}

    with engine.begin() as conn:
        df.head(0).to_sql(table_name, conn, if_exists="replace", index=False, dtype=column_types)

    print(f"Table '{table_name}' créée avec succès.", flush=True)


# -----------------------------------------------------------------------------
def insert_observation(df_observation, table_name):
    if len(df_observation) != 1:
        raise ValueError("df_observation doit contenir une seule ligne.")

    with engine.begin() as conn:
        df_observation.to_sql(table_name, conn, if_exists="append", index=False)

    print("Observation insérée avec succès.", flush=True)


# -----------------------------------------------------------------------------
def insert_dataframe(df, table_name):

    with engine.begin() as conn:
        df.to_sql(table_name, conn, if_exists="append", index=False)
    print(f"Le DataFrame a été inséré avec succès dans la table '{table_name}'.", flush=True)


# -----------------------------------------------------------------------------
def fetch_table_content(table_name):
    with engine.connect() as conn:
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, conn)
    print(df, flush=True)
    return df


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    df = pd.DataFrame({"Name": ["Tom", "Nick", "Krish", "Jack"], "Age": [20, 21, 19, 18]})

    # Création de la table à partir d'un DataFrame initial
    create_table_from_dataframe(df, k_table_name)

    # Insérer le df
    insert_dataframe(df, k_table_name)

    # Insérer une observation
    new_observation = pd.DataFrame([{"Name": "Zoubida", "Age": 42}])
    insert_observation(new_observation, k_table_name)

    fetch_table_content(k_table_name)
