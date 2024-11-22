# Extract from SQL, rows with fraud_confirmed not null (0 or 1)
# Save them in s3://fraud-detection-2-bucket/data/validated.csv (the .csv is overwritten not extended)
# In DEMO_MODE we cheat and we set 25% of the rows in the SQL database with fraud_confirmed not null (see update_fraud_confirmation())

# Can be useful in pgAdmin
# select count(*) FROM fraud_detection_2_table;
# select count(*) FROM fraud_detection_2_table where fraud_confirmed is null;
# select count(*) FROM fraud_detection_2_table where fraud_confirmed is not null;
# UPDATE fraud_detection_2_table SET fraud_confirmed = NULL;


import os
import random
import pandas as pd
from sqlalchemy import create_engine, inspect, Table, MetaData  # text,
from sqlalchemy import func, update, select
from sqlalchemy.engine import Engine


# -----------------------------------------------------------------------------
k_table_name = "fraud_detection_2_table"
k_AWS_S3_CSV = "s3://fraud-detection-2-bucket/data/validated.csv"

# In DEMO_MODE we force 25% of the records to have a non-NULL 'fraud_confirmed' feature
# Otherwise all records having a non-NULL 'fraud_confirmed' feature are used to create the CSV file
k_DEMO_MODE = True

# In DEBUG_MODE we force 1 record have a non-NULL 'fraud_confirmed' feature
k_DEBUG_MODE = True


# -----------------------------------------------------------------------------
def check_table_exist(engine: Engine, table_name: str) -> bool:

    inspector = inspect(engine)
    return inspector.has_table(table_name)


# -----------------------------------------------------------------------------
def get_validated_observations(engine: Engine, table_name: str) -> pd.DataFrame:
    # Extract from SQL rows with fraud_confirmed not null (can be 0 or 1)
    query = f"SELECT * FROM {table_name} WHERE fraud_confirmed IS NOT NULL"
    df = pd.read_sql(query, engine)

    # remove the "is_fraud" feature which is a prediction
    df.drop("is_fraud", inplace=True, axis=1)
    # rename "fraud_confirmed" as "is_fraud"
    df.rename(columns={"fraud_confirmed": "is_fraud", "id": ""}, inplace=True)
    return df


# -----------------------------------------------------------------------------
# TODO : Error Logging - use logging to log errors with timestamps and additional context?
# TODO : Retry Logic - implement a retry mechanism for failed message processing, with exponential backoff and maximum retries to handle transient errors?
# TODO : Asynchronous - use asyncio for improved performance?
# TODO : Batching - No
# TODO : Schema Registry - No
def simulate_fraud_confirmations(engine: Engine, table_name: str) -> None:

    assert k_DEMO_MODE == True, "update_fraud_confirmation() should be call ONLY in DEMO mode."

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)  # Charger la table à partir du nom

    with engine.connect() as conn:
        # Nb of records with `fraud_confirmed` != NULL (0 or 1)
        non_null_count = conn.execute(select(func.count()).where(table.c.fraud_confirmed != None)).scalar()

        # We are in DEMO_MODE see assert above
        # Total number of records
        total_count = conn.execute(select(func.count()).select_from(table)).scalar()

        # How many records need to see their fraud_confirmed to be set to reach a rate of 25% ?
        target_count = int(0.25 * total_count)
        records_to_update = target_count - non_null_count

        if k_DEBUG_MODE:
            records_to_update = 1 if records_to_update else 0

        if records_to_update > 0:
            # get the nb of records with `fraud_confirmed` = NULL to be updated
            rows_to_update = conn.execute(
                select(table.c.id)
                .where(table.c.fraud_confirmed == None)
                .order_by(func.random())  # Random selection
                .limit(records_to_update)
            ).fetchall()

            # Update each of them with random value (0 or 1) in `fraud_confirmed`
            for row in rows_to_update:
                fraud_value = random.choice([True, False])
                conn.execute(update(table).where(table.c.id == row.id).values(fraud_confirmed=fraud_value))
            # for index, row in enumerate(rows_to_update):
            #     if (k_Max_Rows_To_Update != -1) and (index == k_Max_Rows_To_Update):
            #         break
            #     fraud_value = random.choice([True, False])
            #     conn.execute(update(table).where(table.c.id == row.id).values(fraud_confirmed=fraud_value))

        conn.commit()


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    database_url = os.getenv("LOGGER_SQL_URI")
    if database_url is None:
        raise ValueError("LOGGER_SQL_URI environment variable is not set. Did you run ./secrets.ps1 first?")
    engine = create_engine(database_url)

    bExist = check_table_exist(engine, k_table_name)
    if bExist:
        print("The table exists", flush=True)
    else:
        print("The table does'nt exist yet", flush=True)
        exit

    if k_DEMO_MODE:
        simulate_fraud_confirmations(engine, k_table_name)

    df = get_validated_observations(engine, k_table_name)
    print(df)
    df.to_csv(k_AWS_S3_CSV, index=False)
    print(f"Validated dataset includes {len(df)} observations")
