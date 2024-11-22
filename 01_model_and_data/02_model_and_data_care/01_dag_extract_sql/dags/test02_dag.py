# test02_dag.py

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="test02_dag",  # what we see in the Web UI
    default_args=default_args,
    description="Exec BusyBox, wait 10 sec.",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    run_busybox = DockerOperator(
        task_id="run_busybox",
        image="busybox",  # Hello world was too fast, better results when testing with the excellent busybox
        api_version="auto",
        auto_remove=True,  # Remove container once done
        docker_url="tcp://host.docker.internal:2375",  # Connection via TCP
        network_mode="bridge",  # Network mode
        command="sh -c 'echo Starting BusyBox && sleep 10 && echo Stopping BusyBox'",  # Command executed in the container
    )
