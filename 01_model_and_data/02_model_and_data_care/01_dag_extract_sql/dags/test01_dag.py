# test01_dag.py

import ccxt
import json
import logging
from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator


# -----------------------------------------------------------------------------
def fetch_btc_infos() -> None:
    hitbtc = ccxt.hitbtc()
    ticker = hitbtc.fetch_ticker("BTC/USDT")
    now = datetime.now().timestamp()
    filename = f"{now}.json"
    with open(f"./data/{filename}", "w") as f:
        json.dump(ticker, f)
    logging.info(f"BTC dumped into {filename}")


with DAG("test01", start_date=datetime(2024, 1, 1), schedule_interval="@hourly", catchup=False) as dag:
    fetch_btc_infos = PythonOperator(task_id="fetch_btc_infos", python_callable=fetch_btc_infos)
    fetch_btc_infos
