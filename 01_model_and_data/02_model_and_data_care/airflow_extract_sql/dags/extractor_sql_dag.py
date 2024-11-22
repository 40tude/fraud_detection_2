# extractor_sql_dag.py

from airflow.providers.docker.operators.docker import DockerOperator
from airflow import DAG
from datetime import datetime
from docker.types import Mount
from dotenv import dotenv_values

# Charger les variables depuis le fichier .env et en créer une chaine car Airflow ne fait pas son travail
# See env_file=env_vars_str in DockerOperator() while it should be env_file=env_path
# Read this https://github.com/apache/airflow/discussions/29990
env_path = "/home/app/.env"
env_vars_dict = dotenv_values(env_path)  # Retourne un dictionnaire
env_vars_str = "\n".join([f"{key}={value}" for key, value in env_vars_dict.items()])  # Convertir en chaîne

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    "extractor_sql",
    default_args=default_args,
    description="Run extractor SQL script in a Docker container",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    run_extractor = DockerOperator(
        task_id="run_extractor",
        image="extractor_sql_dag_img",
        container_name="extractor_sql_dag",
        command="python /home/app/extractor_03.py",
        env_file=env_vars_str,
        mounts=[
            Mount(source="08_airflow_extractor_sql_dag_shared_app", target="/home/app", type="volume"),
        ],
        network_mode="bridge",
        auto_remove=True,
    )

    run_extractor
