<!-- * Dans cdocker-compose

Lorsqu'un fichier docker-compose.yml est utilisé, Docker interprète les chemins relatifs comme étant basés sur le répertoire dans lequel la commande docker-compose up est exécutée. C'est-à-dire que le chemin relatif spécifié dans la section volumes sera évalué en fonction du répertoire courant (celui d'où vous exécutez la commande).

```
volumes:
      # - ./app:/home/app
      - ../07_modelizer/app:/home/app    
```


```
networks:
  my_network:
    driver: bridge
```

Quand ça démarre faut attendre que modelizer ai récupéré les modèles (15-20 sec)
Quand modelizer fonctionne
1. Le consumer y accède via `k_Modelizer_URL = "http://modelizer:8000/predict"` 
1. On peut accèder avec un browser sur `http://localhost:8000/docs` 

-->



<!-- ###################################################################### -->
<!-- ###################################################################### -->

# Consumer 

Make sure you read the producer [README.md](../03_producer/README.md) file first.



#  ***** Under construction and major update *****
### Do **NOT** spend too much time here while the above warning is there. 



<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Introduction

Remember that the ``consumer`` consumes messages from ``topic_1``, presents them to the ``modelizer``, obtains predictions and saves them in ``topic_2``. In an early version the `consumer` was running the model. This was not a good idea. At present, responsibilities are clearly separated, and ``consumer`` uses an API to make predictions for the model. 

<p align="center">
<img src="./assets/infra02.png" alt="drawing" width="800"/>
<p>


This document covers :
1. Create a Docker image to run ``consumerXY.py``Python scripts which are able to :
    * Read messages from ``topic_1`` 
    * Use an API to present the messages as an input of the model
    * Get predictions from the model
    * Save the message and the prediction in ``topic_2``
1. Testing ``consumerXY.py`` 



<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Create a Docker image to run Python scripts <!-- that can read ``topic_1`` -->

After running a first version of the ``producer`` Python script in the `jedha/confluent-image` image, rather than launching the `test_producerXY.py` script "by hand" from the Linux prompt I tried, without success, to automate its launch (if needed, read again the [README.md](../03_producer/README.md))

After several attempts, the decision was made to create a Docker image using the following "method" :
1. Creating a minimal conda virtual environment using only Python 3.12 (``conda create --name consumer_nodocker python=3.12 -y``)
1. Create a directory and copy the files needed to run `test_producerXY.py` (``secrets.ps1``, ``client.properties``...)
    * At the very beginning `consumer_XY` did not exist yet 
    * Only `test_producerXY.py` was available
1. Add to the virtual environment, the modules required by the Python script (at least, read and write to ``topic_1``)
1. Organize directories to separate what is needed to create the Docker image from the script itself.
1. Anticipate the use of ``docker-compose``. Indeed, at one point, we'll be launching the different components of the ``fraud_detection_2`` application from a single ``docker-compose.yml``. This include, at least, the following components :
    1. the ``producer`` : writes transactions to ``topic_1``
    1. The ``consumer`` : reads from ``topic_1``, requests predictions from the model (MLflow Tracking Server) and writes the inferences to ``topic_2``. 
    1. The ``logger_sql`` : reads from `topic_2` and saves the inferences in a PostgreSQL database, remembering to add a ``fraud_confirmed`` feature.
    1. ...




<!-- ###################################################################### -->
## Organization of subdirectories

Finally (remember CeCe Peniston, 1991 ?), the directories are organized as follows:

```
04_consumer/
│   build_img.ps1
│   docker-compose.yml
│   run_app.ps1
│
├───app
│       ccloud_lib.py
│       client.properties
│       secrets.ps1
│       consumer03.py
│
└───docker
        Dockerfile
        requirements.txt
```
* `build_img.ps1` = a script to create the Docker image
* ``docker-compose.yml`` = application launch orchestration
* `run_app.ps1` = launches the application. Sets passwords, then invokes ``docker-compose.yml``.
* `./app` = the directory containing the ``consumerXY.py`` script. It contains other needed files and `secrets.ps1` (with keys and sensitive parameters)
* ``./docker`` = the directory with the `Dockerfile` and `requirements.txt` files needed to create our own image.


To build the `consumer_img` image, invoke the script :

```
./build_img.ps1

```

This generates a pretty fat `consumer.img` file.

<p align="center">
<img src="./assets/img01.png" alt="drawing" width="800"/>
<p>


The `build_img.ps1` PowerShell script is a one liner. It calls ``docker`` to build `consumer_img` and indicates where to find the Dockerfile. 

The reason why I keep writing one line PowerShell scripts is that they add a "level of indirection" :
* I always invoke the same script (`build_img.ps1`) 
* The content take care of the context : build an image for ``consumerXY.py``, for ``producerXY.py``...
* The same apply to `run_app.ps1`. I run the same command but it launch different modules according the context. 

```
docker build -t consumer_img -f docker/Dockerfile .
```

Here is the content of the Dockerfile

```
FROM python:3.12-slim

WORKDIR /home/app

RUN apt-get update
RUN apt-get install nano unzip
RUN apt install curl -y

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip curl librdkafka-dev && \
    rm -rf /var/lib/apt/lists/* 

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

COPY app/ .

```
* We need the AWS machinery because ``consumerXY.py`` accesses the AWS S3 to read the runs
* We also need to install "by hand" the librdkafka-dev 
* The other modules are listed in the ``requirements.txt`` file



Here below the `requirements.txt` file

```
# same as producer
requests
pandas

# librdkafka is managed with apt-get
confluent_kafka 
avro-python3

# required to execute the model
mlflow
boto3 
imbalanced-learn

```



<!-- ###################################################################### -->
## Comments 
* `imbalanced-learn` is on the last line. 
* Indeed the model, which is on the MLflow Tracking Server use SMOTE.
* It's **important** to bear in mind that if the template uses another ML module, the latter will need to be added to the ``requirements.txt`` file, so that once the model has been downloaded, you can run it in the context of the Docker image.   

At the end of the build process, we have a docker image that we can use in a ``docker-compose.yml`` configuration. Here is the ``.yml`` file :

```
services:
  consumer:
    image: consumer_img
    build: /docker
    container_name: consumer
    environment:
      - SASL_USERNAME=${SASL_USERNAME}
      - SASL_PASSWORD=${SASL_PASSWORD}
      - AWS_REGION=${AWS_REGION}  
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}  
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}  
      - SMTP_USER=${SMTP_USER}  
      - SMTP_PASSWORD=${SMTP_PASSWORD}  
      - SMTP_SERVER=${SMTP_SERVER}  
      - SMTP_PORT=${SMTP_PORT}  
      - EMAIL_RECIPIENT=${EMAIL_RECIPIENT}  
    volumes:
      - ./app:/home/app              
    working_dir: /home/app
    command: python consumer03.py
```
* Pay attention to the very last line. I use to have different version of ``consumerXY.py``. If you create a new version of the script, make sure to update this line
* There are many environment variables passed because most of them should not be public.
* The good news is that to run the ``consumerXY.py`` one just need to invoke ``.\run_app.ps1``

Here is the ``./app/secrets.ps1`` file :
```
# topic access confluent
$env:SASL_USERNAME = "6KQ..."
$env:SASL_PASSWORD = "zBV..."

# fraud-detection-2-user full access S3
$env:AWS_REGION             = "eu-west-3"
$env:AWS_ACCESS_KEY_ID      = "AKI..."
$env:AWS_SECRET_ACCESS_KEY  = "vtL..."

# Email
$env:SMTP_USER          = "phil..."
$env:SMTP_PASSWORD      = "..."
$env:SMTP_SERVER        = 'smtp...'
$env:SMTP_PORT          = '587'
$env:EMAIL_RECIPIENT    = "phil..."

```

Here is the `run_app.ps1` PowerShell script

```powershell
. "./app/secrets.ps1"
docker-compose up -d
```

It is 2 lines :
1. run the ``./app/secrets.ps1`` script to make sure the environment variables are set (remember that ``secrets.ps1`` is in ``.gitignore`` so no secret key becomes public)
1. invoque ``docker-compose`` which use the content of ``docker-compose.yml``



<!-- ###################################################################### -->
## Comments
1. Again. Take the time to study the contents of the directories and files. 
1. While building the Docker image, one annoying thing is that a `librdkafka` library is required, but it has to be installed via an `apt-get` (see the content of `Dockerfile`).
1. As for the “method” of creating a conda virtual environment, a directory, and launching the module code in this context... It's a bit cumbersome, consuming disk space and time. On the other hand, at the end you know exactly what's in the Docker image and you're able to make relatively lite images.  
1. As far as the organization of subdirectories and the naming convention for scripts are concerned, I think I'll keep it in future modules (``logger_sql`` ...).
1. I think I'll also continue to use docker-compose regularly even if I only have one application to run. 
1. Indeed, this organization makes a clear separation between the construction of the image and the context to be set up to run the application in the image. Finally, if need be, we have the elements to launch the application with others from a more substantial ``docker-compose.yml``. 







<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Testing ``consumerXY.py`` 

Run the ``consumerXY.py`` script in the Docker image with the following command :

```
./run_app.ps1

```

Via the `run_app.ps1`, the consumer in launched in **detached mode**. This is why we don't see anything in the current terminal. We must use ``docker-compose`` commands to :
* list the running process (``docker-compose ps``)
* inspect the logs (`docker-compose logs consumer`) 
* gently close the app (`docker-compose down consumer`)

<p align="center">
<img src="./assets/img02.png" alt="drawing" width="800"/>
<p>

If, for any reason, you have doubts about the output you get in the terminal with `docker-compose logs consumer`, run the command `docker-compose logs consumer` twice (or more). Indeed, outputs are buffered so they may take some time. On the other hand feel free to use Docker Desktop to inspect the output.

<p align="center">
<img src="./assets/img025.png" alt="drawing" width="800"/>
<p>


The reason we can read messages from ``topic_1`` is simply because we previously used the ``test_producerXY.py`` to send them there. In fact, ``topic_1`` act as a backlog for 7 days.


<p align="center">
<img src="./assets/img03.png" alt="drawing" width="800"/>
<p>

Among the text in the console we can read :

```
consumer  | Received msg : {"columns": ["trans_date_trans_time", "cc_num", "merchant", "category", "amt", "first", "last", "gender", "street", "city", "state", "zip", "lat", "long", "city_pop", "job", "dob", "trans_num", "unix_time", "merch_lat", "merch_long", "is_fraud"], "index": [144842], "data": [["2024-10-31 15:56:25", 377895991033232, "fraud_McDermott, Osinski and Morar", "home", 16.18, "Kimberly", "Myers", "F", "6881 King Isle Suite 228", "Higganum", "CT", 6441, 41.4682, -72.5751, 5438, "Librarian, academic", "1964-11-17", "64b632ebfbc52a1075747f9301db22b8", 1730390185811, 41.581898, -73.130293, 0]]}
```

This means that the script is able to read a transaction from ``topic_1``. 

Later on we can see :  


```
consumer  | URI of the run : runs:/c98b623712854dd5abf068758efc0d11/model
consumer  | Prediction : Not Fraud
```

This means that the script is able to 
1. contact MLflow Tracking Server
1. find the most recent "experiment" and find the latest "run" in there  
1. download the run 
1. submit the read from ``topic_1`` as an input to the downloaded model and get a prediction. 
    * Indeed, the last line above says ``Not Fraud``

The last 2 messages explain that the record plus the inference are now logged on ``topic_2`` 

```
consumer  | Produced record to topic topic_2 partition [5] @ offset 14
consumer  | Consumer is done
```

This means that in ``topic_2``, the folling information are saved :  
1. the record from ``topic_1``
1. plus the inference
1. plus a new ``fraud_confirmed`` feature 
    * This feature will be used to extend the training dataset if and only if it is updated after investigation and confirmation


If one go to [confluent](https://confluent.cloud/) he can double check the content of ``topic_2``

<p align="center">
<img src="./assets/img031.png" alt="drawing" width="800"/>
<p>

This is not demonstrated here but with ``consumer03.py`` and above, the script can :
* Either use the model of the last run or the model of the one before last run (rollback)
    * A mechanism avoids downloading the model of the desired “run” if it is already available locally.
    * Indeed I suspect roolbacks will be seldom. 
    * More often, once downloaded the model of the last run will be used again and again to make inferences
* If a fraudulent transaction is inferred an email is sent 
    * The parameters are found in ``secrets.ps1``
    * The attached ``.csv`` file contains all transaction information  

<p align="center">
<img src="./assets/img032.png" alt="drawing" width="800"/>
<p>



<!-- ###################################################################### -->
<!-- ###################################################################### -->
# What's next ? 

* The next version of ``consumerXY.py`` should be based on an infinite loop 
    * Like it is done in ``producerXY.py``
* As I write this ``README.md``, nothing has been decided yet, but I'm wondering if ``producer``, ``consumer`` and others modules shouldn't be Flask applications. The point is that we could call them to pass them parameters, ask them to return a status. Once again, it's just an idea and nothing has been decided yet. 
* The priority is to run ``logger_sql``, which will read the content of ``topic_2`` and save it in an SQL database.
* Go to the directory `05_logger_sql` and read the [README.md](../05_logger_sql/README.md) file. 
    * The previous link to the next README.md to read may not work on GitHub but it works like a charm locally in VSCode or a Web browser.

































