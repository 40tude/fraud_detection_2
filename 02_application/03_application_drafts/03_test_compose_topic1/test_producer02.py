# Colonnes du fichier fraud_test.csv
# vide         ,trans_date_trans_time  ,cc_num          ,merchant               ,category       ,amt   ,first   ,last    ,gender  ,street             ,city      ,state  ,zip  ,lat      ,long     ,city_pop   ,job                ,dob         ,trans_num                         ,unix_time   ,merch_lat  ,merch_long   ,is_fraud
# 0        ,2020-06-21 12:14:25    ,2291163933867244,fraud_Kirlin and Sons  ,personal_care  ,2.86  ,Jeff    ,Elliott ,M       ,351 Darlene Green  ,Columbia  ,SC     ,29209,33.9659  ,-80.9355 ,333497     ,Mechanical engineer,1968-03-19  ,2da90c7d74bd46a0caf3777415b3ebd3  ,1371816865  ,33.986391  ,-81.200714   ,0


# Colonnes du fichier fraud_test.csv (transformé en .xlsx)
# Column1	trans_date_trans_time	cc_num	merchant	category	amt	first	last	gender	street	city	state	zip	lat	long	city_pop	job	dob	trans_num	unix_time	merch_lat	merch_long	is_fraud

# Données lues brutes
# {"columns":["cc_num","merchant","category","amt","first","last","gender","street","city","state","zip","lat","long","city_pop","job","dob","trans_num","merch_lat","merch_long","is_fraud","current_time"],"index":[301199],"data":[[4497913965512794052,"fraud_Berge, Kautzer and Harris","personal_care",60.16,"Scott","Edwards","M","838 Amy Street Suite 107","Pembroke","NC",28372,34.6902,-79.1834,14783,"Hospital doctor","1955-11-07","3cb54a489fb351f73a7db98f6c7bb1ad",34.38451,-78.621062,0,1730134684025]]}

# "cc_num","merchant","category","amt","first","last","gender","street","city","state","zip","lat","long","city_pop","job","dob","trans_num","merch_lat","merch_long","is_fraud","current_time"
# cc_num,merchant,category,amt,first,last,gender,street,city,state,zip,lat,long,city_pop,job,dob,trans_num,merch_lat,merch_long,is_fraud,current_time
# 21 colonnes


# Colonnes du fichier fraud_test.csv
#          ,trans_date_trans_time  ,cc_num,merchant    ,category   ,amt,first  ,last   ,gender ,street ,city   ,state  ,zip,lat,long   ,city_pop   ,job,dob,trans_num  ,unix_time  ,merch_lat  ,merch_long ,is_fraud
# Sortie de quick_test.ipnb
# 	        trans_date_trans_time	cc_num merchant	    category	amt	first	last	gender	street	city	state	zip	lat	long	city_pop	job	dob	trans_num	unix_time	merch_lat	merch_long	is_fraud


import time
import json
import requests
import ccloud_lib
import pandas as pd
from datetime import datetime, timezone
from confluent_kafka import Producer, Message

k_Topic = "topic_1"
k_Client_Prop = "client.properties"
k_RT_Data_Producer = "https://real-time-payments-api.herokuapp.com/current-transactions"


def acked(err: int, msg: Message) -> None:
    global delivered_records
    # Delivery report handler called on successful or failed delivery of message
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        delivered_records += 1
        print(f"Produced record to topic {msg.topic()} partition [{msg.partition()}] @ offset {msg.offset()}")


def fetch_and_store() -> None:

    while True:
        try:
            response = requests.get(k_RT_Data_Producer)
            response.raise_for_status()  # Checks if the request was successful

            # convertit le contenu de la réponse (qui est au format JSON) en un objet Python (list, dico...)
            data = response.json()

            # vérifie si data est une chaîne de caractères
            # En fonction de la configuration de l'API
            # le contenu peut être renvoyé sous forme de chaîne JSON (texte brut) plutôt que directement sous forme de dictionnaire.
            # Si data est une chaîne, json.loads(data) convertit cette chaîne en un objet JSON Python (dictionnaire ou liste).
            if isinstance(data, str):
                data = json.loads(data)

            columns = data["columns"]
            index = data["index"]
            rows = data["data"]

            df = pd.DataFrame(data=rows, index=index, columns=columns)

            # ! 17 is hard coded
            # TODO : find a better way
            col = df["current_time"]
            df.insert(17, "unix_time", col)

            # convert to date string
            df.rename(columns={"current_time": "trans_date_trans_time"}, inplace=True)
            timestamp = df["trans_date_trans_time"].iloc[0]
            date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            str_date = date.strftime("%Y-%m-%d %H:%M:%S")

            df["trans_date_trans_time"] = df["trans_date_trans_time"].astype(str)
            df.at[index[0], "trans_date_trans_time"] = str_date

            # Modifies the order of columns in the df DataFrame
            # Moving the last column to the first position
            # Leaving all other columns in their original order
            cols = df.columns.tolist()
            reordered_cols = [cols[-1]] + cols[:-1]  # the last col then all the other until the before last col
            df = df[reordered_cols]

            data = {"columns": df.columns.tolist(), "index": df.index.tolist(), "data": df.values.tolist()}

            # Convertit le dictionnaire data en JSON et encode en UTF-8
            producer.produce(k_Topic, key="dummy", value=json.dumps(data).encode("utf-8"), on_delivery=acked)
            print(f"Data sent: {data}")
        except requests.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        time.sleep(15)


if __name__ == "__main__":

    # Initialize configurations from "python.config" file
    conf = ccloud_lib.read_ccloud_config(k_Client_Prop)

    # Create Producer instance
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)

    # Create topic if it doesn't already exist
    ccloud_lib.create_topic(conf, k_Topic)

    fetch_and_store()
