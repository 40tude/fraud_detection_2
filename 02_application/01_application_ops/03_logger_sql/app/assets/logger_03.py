import os
import json
import time
import ccloud_lib
import pandas as pd
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, text, inspect
from confluent_kafka import Consumer, KafkaException

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


# Colonne 'trans_date_trans_time': object
# Colonne 'cc_num': int64
# Colonne 'merchant': object
# Colonne 'category': object
# Colonne 'amt': float64
# Colonne 'first': object
# Colonne 'last': object
# Colonne 'gender': object
# Colonne 'street': object
# Colonne 'city': object
# Colonne 'state': object
# Colonne 'zip': int64
# Colonne 'lat': float64
# Colonne 'long': float64
# Colonne 'city_pop': int64
# Colonne 'job': object
# Colonne 'dob': object
# Colonne 'trans_num': object
# Colonne 'unix_time': int64
# Colonne 'merch_lat': float64
# Colonne 'merch_long': float64
# Colonne 'is_fraud': int64

k_Topic_2 = "topic_2"
k_GroupId = "python-group-2"
k_Client_Prop = "client.properties"

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
    unix_time BIGINT,
    merch_lat FLOAT,
    merch_long FLOAT,
    is_fraud BOOLEAN,
    fraud_confirmed BOOLEAN DEFAULT NULL
);"""


# -----------------------------------------------------------------------------
def read_transaction_from_topic_2(consumer: Consumer) -> Optional[pd.DataFrame]:  # Union[pd.DataFrame, None]
    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            json_str = msg.value().decode("utf-8")
            print(f"Received msg : {json_str}\n\n", flush=True)

            try:
                # json_dict = json.loads(json_str)
                # print("json_dict : ", json_dict)
                # return None
                data_list = json.loads(json_str)  # JSON vers liste de dictionnaires
                df = pd.DataFrame(data_list)  # Liste de dicts vers DataFrame
                df["is_fraud"] = df["is_fraud"].astype(bool)
                # print(df)
                # df = pd.DataFrame(data=json_dict["data"], columns=json_dict["columns"], index=json_dict["index"])
                return df
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error in JSON format : {e}", flush=True)
                continue

    except KeyboardInterrupt:
        print("CTRL+C detected. Closing gently.", flush=True)

    finally:
        consumer.close()

    return None


# -----------------------------------------------------------------------------
def create_topic_consumer() -> Consumer:

    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)

    # defines the ID of the consumer group to which the consumer belongs
    conf["group.id"] = k_GroupId

    # the consumer starts reading at the beginning if no offset has been recorded for him or continue to read from where he left off.
    # ! The offset for each partition is stored at group level, NOT at individual consumer level.
    # So a consumer joining the same group will pick up where the last one left off
    # If you change the group name (python-group-42), the user will read the earliest message.
    conf["auto.offset.reset"] = "earliest"

    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    consumer = Consumer(consumer_conf)
    consumer.subscribe([k_Topic_2])
    return consumer


# -----------------------------------------------------------------------------
def check_table_exist(engine: Engine, table_name: str) -> bool:

    inspector = inspect(engine)
    return inspector.has_table(table_name)


# -----------------------------------------------------------------------------
def create_table(engine: Engine) -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text(k_SQL_Create_Table))
            conn.commit()
            # print("Table created successfully.")
    except SQLAlchemyError as error:
        print(f"An error occurred: {error}")


# -----------------------------------------------------------------------------
def insert_observation(engine: Engine, observation_df: pd.DataFrame, table_name: str) -> None:
    if len(observation_df) != 1:
        raise ValueError("df_observation doit contenir une seule ligne.")

    with engine.begin() as conn:
        observation_df.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()

    # print("Observation insérée avec succès.", flush=True)


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    print("Logger SQL started", flush=True)

    database_url = os.getenv("LOGGER_SQL_URI")
    engine = create_engine(database_url)
    bExist = check_table_exist(engine, k_table_name)
    if not bExist:
        create_table(engine)
        print("The table has been created", flush=True)
    else:
        print("The table already exists", flush=True)

    consumer = create_topic_consumer()
    try:
        current_transaction_df = read_transaction_from_topic_2(consumer)
        print(current_transaction_df, flush=True)
    except KafkaException as e:
        print(f"Kafka error : {e}", flush=True)

    insert_observation(engine, current_transaction_df, k_table_name)

    print("Logger SQL will be done in 5 sec", flush=True)
    time.sleep(5)
