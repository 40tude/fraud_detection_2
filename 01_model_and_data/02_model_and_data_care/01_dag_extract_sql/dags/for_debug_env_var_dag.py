import os
import logging
from airflow import DAG
from datetime import datetime
from dotenv import load_dotenv
from airflow.models import Variable
from airflow.operators.python import PythonOperator


# -----------------------------------------------------------------------------
def get_my_env_var() -> None:
    env_path = "/home/app/.env"
    load_dotenv(env_path)

    try:
        bob = Variable.get("LOGGER_SQL_URI")  # Try to get the value from Airflow config
    except KeyError:
        bob = "Undefined"
    my_LOGGER_SQL_URI = os.getenv("LOGGER_SQL_URI", bob)
    logging.info(f"LOGGER_SQL_URI = {my_LOGGER_SQL_URI}")

    my_AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    logging.info(f"AWS_SECRET_ACCESS_KEY = {my_AWS_SECRET_ACCESS_KEY}")

    my_AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    logging.info(f"AWS_ACCESS_KEY_ID = {my_AWS_ACCESS_KEY_ID}")


with DAG(
    "debug_env_var_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    debug_env_var_task = PythonOperator(
        task_id="debug_env_var_task",
        python_callable=get_my_env_var,
    )
