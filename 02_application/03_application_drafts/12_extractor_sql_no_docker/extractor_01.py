# Read from SQL
# save as s3://fraud-detection-2-bucket/data/validated.csv

import os

# import json
# import time
# import ccloud_lib
import pandas as pd

# from typing import Optional
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy import create_engine, text, inspect
from sqlalchemy import create_engine, inspect  # text,

# from confluent_kafka import Consumer, KafkaException


k_table_name = "fraud_detection_2_table"
k_AWS_S3_CSV = "s3://fraud-detection-2-bucket/data/validated.csv"


# -----------------------------------------------------------------------------
def check_table_exist(engine, table_name: str) -> bool:

    inspector = inspect(engine)
    return inspector.has_table(table_name)


# -----------------------------------------------------------------------------
def get_validated_observations(engine, table_name):
    query = f"SELECT * FROM {table_name} WHERE fraud_confirmed IS NOT NULL"
    df = pd.read_sql(query, engine)

    # remove the "is_fraud" feature which is a prediction
    df.drop("is_fraud", inplace=True, axis=1)
    # rename "fraud_confirmed" as "is_fraud"
    df.rename(columns={"fraud_confirmed": "is_fraud", "id": ""}, inplace=True)
    return df


# -----------------------------------------------------------------------------
# ! TESTING ONLY
def get_all_observations(engine, table_name):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, engine)

    # remove the "is_fraud" feature which is a prediction
    df.drop("is_fraud", inplace=True, axis=1)
    # rename "fraud_confirmed" as "is_fraud"
    df.rename(columns={"fraud_confirmed": "is_fraud", "id": ""}, inplace=True)

    # replace Null with 1 in "is_fraud"
    df["is_fraud"] = df["is_fraud"].fillna(1)

    return df


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    print("Extractor SQL started", flush=True)

    database_url = os.getenv("LOGGER_SQL_URI")
    engine = create_engine(database_url)
    bExist = check_table_exist(engine, k_table_name)
    if bExist:
        print("The table exists", flush=True)
    else:
        print("The table does'nt exist yet", flush=True)

    # insert_observation(engine, current_transaction_df, k_table_name)
    df = get_all_observations(engine, k_table_name)
    print(df)
    df.to_csv("./all_observations.csv", index=False)
    df.to_csv(k_AWS_S3_CSV, index=False)

    print("Extractor SQL is over", flush=True)


# -----------------------------------------------------------------------------
# def read_transaction_from_topic_2(consumer: Consumer) -> Optional[pd.DataFrame]:  # Union[pd.DataFrame, None]
#     try:
#         while True:
#             msg = consumer.poll(1.0)

#             if msg is None:
#                 continue

#             if msg.error():
#                 raise KafkaException(msg.error())

#             json_str = msg.value().decode("utf-8")
#             print(f"Received msg : {json_str}\n\n", flush=True)

#             try:
#                 # json_dict = json.loads(json_str)
#                 # print("json_dict : ", json_dict)
#                 # return None
#                 data_list = json.loads(json_str)  # JSON vers liste de dictionnaires
#                 df = pd.DataFrame(data_list)  # Liste de dicts vers DataFrame
#                 df["is_fraud"] = df["is_fraud"].astype(bool)
#                 # print(df)
#                 # df = pd.DataFrame(data=json_dict["data"], columns=json_dict["columns"], index=json_dict["index"])
#                 return df
#             except (json.JSONDecodeError, KeyError) as e:
#                 print(f"Error in JSON format : {e}", flush=True)
#                 continue

#     except KeyboardInterrupt:
#         print("CTRL+C detected. Closing gently.", flush=True)

#     finally:
#         consumer.close()

#     return None


# -----------------------------------------------------------------------------
# def insert_observation(engine, observation_df, table_name):
#     if len(observation_df) != 1:
#         raise ValueError("df_observation doit contenir une seule ligne.")

#     with engine.begin() as conn:
#         observation_df.to_sql(table_name, conn, if_exists="append", index=False)
#         conn.commit()

#     # print("Observation insérée avec succès.", flush=True)


# -----------------------------------------------------------------------------
# def create_topic_consumer() -> Consumer:

#     conf = ccloud_lib.read_ccloud_config(k_Client_Prop)

#     # defines the ID of the consumer group to which the consumer belongs
#     conf["group.id"] = k_GroupId

#     # the consumer starts reading at the beginning if no offset has been recorded for him or continue to read from where he left off.
#     # ! The offset for each partition is stored at group level, NOT at individual consumer level.
#     # So a consumer joining the same group will pick up where the last one left off
#     # If you change the group name (python-group-42), the user will read the earliest message.
#     conf["auto.offset.reset"] = "earliest"

#     consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
#     consumer = Consumer(consumer_conf)
#     consumer.subscribe([k_Topic_2])
#     return consumer


# -----------------------------------------------------------------------------
# def create_table(engine) -> None:
#     try:
#         with engine.connect() as conn:
#             conn.execute(text(k_SQL_Create_Table))
#             conn.commit()
#             # print("Table created successfully.")
#     except SQLAlchemyError as error:
#         print(f"An error occurred: {error}")
