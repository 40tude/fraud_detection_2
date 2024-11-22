# Read from SQL
# save as s3://fraud-detection-2-bucket/data/validated.csv

import os
import random
import pandas as pd
from sqlalchemy import create_engine, inspect, Table, MetaData  # text,
from sqlalchemy import func, update, select

# -----------------------------------------------------------------------------
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
