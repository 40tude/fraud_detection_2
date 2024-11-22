# What is on confluent ?
# [
#   {
#     "trans_date_trans_time": "2024-10-31 15:56:44",
#     "cc_num": 6511349151405438,
#     "merchant": "fraud_Donnelly LLC",
#     "category": "entertainment",
#     "amt": 37.79,
#     "first": "Robert",
#     "last": "Nguyen",
#     "gender": "M",
#     "street": "74835 Garner Point",
#     "city": "Ruth",
#     "state": "NV",
#     "zip": 89319,
#     "lat": 39.3426,
#     "long": -114.8859,
#     "city_pop": 450,
#     "job": "Interpreter",
#     "dob": "1946-08-24",
#     "trans_num": "41f7ed98cf5507e8cadef195eb1df340",
#     "unix_time": 1730390204121,
#     "merch_lat": 40.206445,
#     "merch_long": -114.418492,
#     "is_fraud": 0,
#     "fraud_confirmed": null
#   }
# ]

import os
import time
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

k_table_name = "fraud_detection_2_table"
k_SQL_Create_Table = f"""CREATE TABLE IF NOT EXISTS {k_table_name} (
    id SERIAL PRIMARY KEY,
    trans_date_trans_time TIMESTAMP,
    cc_num BIGINT,
    merchant VARCHAR(255),
    category VARCHAR(50),
    amt FLOAT,
    first VARCHAR(50),
    last VARCHAR(50),
    gender CHAR(1),
    street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip INTEGER,
    lat FLOAT,
    long FLOAT,
    city_pop INTEGER,
    job VARCHAR(100),
    dob DATE,
    trans_num VARCHAR(255) UNIQUE,
    unix_time INTEGER,
    merch_lat FLOAT,
    merch_long FLOAT,
    is_fraud BOOLEAN,
    fraud_confirmed BOOLEAN DEFAULT NULL
);"""


# -----------------------------------------------------------------------------
def check_table_exist(engine, table_name: str) -> bool:

    inspector = inspect(engine)
    return inspector.has_table(table_name)


# -----------------------------------------------------------------------------
def create_table(engine) -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text(k_SQL_Create_Table))
            conn.commit()
            # print("Table created successfully.")
    except SQLAlchemyError as error:
        print(f"An error occurred: {error}")


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    print("Logger SQL started", flush=True)

    database_url = os.getenv("LOGGER_SQL_URI")
    engine = create_engine(database_url)
    bExist = check_table_exist(engine, k_table_name)
    if not bExist:
        create_table(engine)
        # Vérification après tentative de création
        if check_table_exist(engine, k_table_name):
            print("The table has been successfully created", flush=True)
        else:
            print("Table creation failed", flush=True)
    else:
        print("The table already exists", flush=True)

    print("Logger SQL is done", flush=True)
