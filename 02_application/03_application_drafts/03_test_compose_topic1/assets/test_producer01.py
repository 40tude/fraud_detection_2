# Colonnes du fichier fraud_test.csv
#          ,trans_date_trans_time  ,cc_num,merchant    ,category   ,amt,first  ,last   ,gender ,street ,city   ,state  ,zip,lat,long   ,city_pop   ,job,dob,trans_num  ,unix_time  ,merch_lat  ,merch_long ,is_fraud

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
import requests
from confluent_kafka import Producer, Message
import ccloud_lib

k_Topic = "topic_1"
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
            data = response.json()
            producer.produce(k_Topic, key="dummy", value=data.encode("utf-8"), on_delivery=acked)
            print(f"Data sent: {data}")
        except requests.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        time.sleep(15)


if __name__ == "__main__":

    # Initialize configurations from "python.config" file
    conf = ccloud_lib.read_ccloud_config("client.properties")

    # Create Producer instance
    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    producer = Producer(producer_conf)

    # Create topic if it doesn't already exist
    ccloud_lib.create_topic(conf, k_Topic)

    fetch_and_store()
