# Read from SQL
# save as s3://fraud-detection-2-bucket/data/validated.csv

import os
import random
import pandas as pd
from sqlalchemy import create_engine, inspect, Table, MetaData  # text,
from sqlalchemy import func, update, select


# import json
# import time
# import ccloud_lib
# from typing import Optional
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy import create_engine, text, inspect


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
# 25 % of the records will have an updated "fraud_confirmed" updated (0 or 1)
def update_fraud_confirmation(engine, table_name):

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)  # Charger la table à partir du nom

    with engine.connect() as conn:
        # Total number of records
        total_count = conn.execute(select(func.count()).select_from(table)).scalar()

        # Nb of records with `fraud_confirmed` != NULL (0 or 1)
        non_null_count = conn.execute(select(func.count()).where(table.c.fraud_confirmed != None)).scalar()

        # How many records need to be updatedto reach 25% ?
        target_count = int(0.25 * total_count)
        records_to_update = target_count - non_null_count

        if records_to_update > 0:
            # get the nb of records with `fraud_confirmed` = NULL to be updated
            rows_to_update = conn.execute(
                select(table.c.id)
                .where(table.c.fraud_confirmed == None)
                .order_by(func.random())  # Sélection aléatoire
                .limit(records_to_update)
            ).fetchall()

            # Update each of them with random value (0 or 1) in `fraud_confirmed`
            for row in rows_to_update:
                fraud_value = random.choice([True, False])
                conn.execute(update(table).where(table.c.id == row.id).values(fraud_confirmed=fraud_value))

        conn.commit()


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    database_url = os.getenv("LOGGER_SQL_URI")
    engine = create_engine(database_url)

    bExist = check_table_exist(engine, k_table_name)
    if bExist:
        print("The table exists", flush=True)
    else:
        print("The table does'nt exist yet", flush=True)

    update_fraud_confirmation(engine, k_table_name)
    df = get_validated_observations(engine, k_table_name)
    print(df)
    # df.to_csv('./all_observations.csv', index=False)
    df.to_csv(k_AWS_S3_CSV, index=False)


# -----------------------------------------------------------------------------
# ! TESTING ONLY
# def get_all_observations(engine, table_name):
#     query = f"SELECT * FROM {table_name}"
#     df = pd.read_sql(query, engine)

#     # remove the "is_fraud" feature which is a prediction
#     df.drop("is_fraud", inplace=True, axis=1)
#     # rename "fraud_confirmed" as "is_fraud"
#     df.rename(columns={"fraud_confirmed": "is_fraud", "id": ""}, inplace=True)

#     # replace Null with 1 in "is_fraud"
#     df["is_fraud"] = df["is_fraud"].fillna(1)

#     return df


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
