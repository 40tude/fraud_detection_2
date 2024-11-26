<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Introduction 

* At the end of the day, we want to use a model to predict fraudulent payments in real-time and respond appropriately.
    * Initial [specifications](https://app.jedha.co/course/final-projects-l/automatic-fraud-detection-l)
* At a very high level, here is the spirit of the architecture and how it works :
    * On the right hand side transactions happen in "realtime" (Real-Time Data Producer block)  
    * They are read in the Consume Data block.
    * Then used to make inferences (MLflow block)
    * Once inferences are done
        * If a fraudulent transaction is detected then an alert is raised (e-mail)
        * All transactions (with associated inference result) are stored in a database (Store data block)
    * Once in the database, records can be used for analysis (Leverage Data block)
    * On the left hand side, a train dataset is used to train the model (Build algorithm block)
        * There is an option to, over the time, extend the training dataset with new validated records (coming from the database)

<!-- "real time" or "realtime" is used as a noun (and can also be used as an adjective) but "real-time" is used as an adjective only -->

Schema from the initial specifications :

<p align="center">
<img src="./assets/img01.png" alt="drawing" width="800"/>
<p>


See below how it has been translated today :

<p align="center">
<img src="./assets/img03.png" alt="drawing" width="800"/>
<p>

## Explanations  
* Each yellow block in the figure above represents a module running in a Docker image.
   * Each module is started with a Docker Compose file.
   * The goal is to eventually have a "master" Docker Compose orchestration file to start all components together.
* **Left-hand side:** Transactions are fetched by the `producer` module. It’s called `producer` because it "produces" messages stored in a Kafka topic on Confluent. In short, a topic is a smart, scalable buffer. The production occurs at `speed_1`, meaning this task operates asynchronously from the rest of the application. For example, even if the rest of the application is paused, data storage in `topic_1` continues (the reverse is also true).
* The last comment about ``speed_1`` applies to all other speeds in the architecture above. The idea is to have a system that is relatively resilient.
* At `speed_2`, the (misnamed) `consumer` module reads records from `topic_1`. It submits these messages to the `modelizer` module, which returns a prediction (fraud or not fraud). If fraud is detected, an alert is sent via email with the fraudulent transaction attached. Finally, the initial message and prediction are stored in `topic_2`.
* `modelizer` (above `consumer` in the figure) is a module exposing models (latest and previous versions) through an API, allowing for predictions and rollback operations. It retrieves the last two models version by querying the MLflow server. This is why here the speed is "On request".
* **Right-hand side:** The `logger_SQL` module reads messages from `topic_2` at `speed_3` and saves them to a PostgreSQL database hosted on Heroku. This database acts as a data warehouse, and end users can query it using tools like Excel, Power BI, and Tableau.
* We can assume that fraudulent transactions are reviewed. Once we verify whether a predicted fraudulent transaction was indeed fraudulent, the database content can be updated by other end users. The same applies if transactions labeled "not fraud" by the model are reviewed. With confirmation, the database can be updated accordingly.
* The `extractor_SQL` module extracts records from the database that have been confirmed. It generates a `validated` dataset that extends the original `training` dataset. The rate is once per day  (Daily). Mostly for cost reasons, both datasets (``training`` & ``validated``) are stored in 2 separate AWS S3 buckets.
* **Top of the figure:** The `train` module combines both datasets (training and validated) to train the models. Performance metrics, artifacts, and models are tracked on an MLflow Tracking server hosted on Heroku, while the models and artifacts are stored in an AWS S3 bucket. The `train` module performs a single function: training models. It does not push or share models with `modelizer`, for example.

## In addition
The project also includes :
* Testing (pytest)
* CI/CD with Jenkins
* Monitoring with Evidently
* ...


<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Notes on how ``REAME.md`` files are written
* In this ``README.md``, as well as some of the others documentation files, screen captures may include information relative to the previous version project. That shouldn't prevent you from understanding the point.
* Most of the ``README.md`` are written so that you can rebuild the project on your own
    * This is why, quite often, they look like "recipe". 
    * This is made on purpose.
    * They are also a way for me to keep my own notes and put down, black on white, what I think I've understood at the time of writing.
    * Finally the ``README.md`` are also a kind of "journal" while I'm working on the project :
        * Indeed, I realize that I iterate quite a lot: new ideas, optimizations, architecture, tools. 
        * In short, I like to keep track of my thoughts throughout the project. 





<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Getting re-started

* I'm an happy user of Windows 11 and Conda. 
* Some of the steps below may slightly defer if you live with a Linux based system
* Open a terminal in a directory where you will be able to create a directory to host the project  


<!-- ###################################################################### -->
## Side Note
* Below I do not make a fork of the previous project
* This is because I'm not really interested by the future versions of the [fraud_detection_1](https://github.com/40tude/fraud_detection)
* Also, I delete the ``./git`` directory because, for me, ``fraud_detection_2`` is a brand new adventure.
    * I could be completely wrong with this way of thinking. 
    * I don't feel expert enough to have a definitive opinion on this point.


```bash
git clone https://github.com/40tude/fraud_detection.git
mv ./fraud_detection/ ./fraud_detection_2/
cd ./fraud_detection_2/
Remove-Item ./.git/ -Recurse
conda create --name fraud2 python=3.12 -y
conda activate fraud2
code .
```


<!-- ###################################################################### -->
## Install mypy  
* From the VSCode integrated terminal  
* If necessary, take a look at this [documentation](https://mypy.readthedocs.io/en/stable/getting_started.html#strict-mode-and-configuration)  

```bash
conda install mypy -y 
```

* At the root of the project, create `mypy.ini` containing :

```
[mypy]
python_version = 3.12  
ignore_missing_imports = True
strict = True
warn_return_any = True
warn_unused_ignores = True
show_error_codes = True
color_output = True
```

* You may not agree, with the here above options
* Here too i'm not definitive. Feel free to adapt them to your context



<!-- ###################################################################### -->
## Get the train data
* Create the directory `./data` at the root of the project  
* Get a copy of `fraud_test.csv` from this [page](https://app.jedha.co/course/final-projects-l/automatic-fraud-detection-l)
* Drop the ``.csv`` file in ``./data``

### Note
* If, for any reason, you can't get the ``.csv`` file from the previous page... No worry.
* In the Notebook used for the EDA (see below) you can either get the data from a local copy or from a public AWS S3 bucket.
* Comment/uncomment the option you need 
* As a last option you can get a copy of the `.csv` on this [page](https://real-time-payments-api.herokuapp.com/)

```python
filename_in = Path(k_AssetsDir)/k_FileName
df = pd.read_csv(filename_in)

# Alternative (AWS S3 bucket)
# df = pd.read_csv("https://lead-program-assets.s3.eu-west-3.amazonaws.com/M05-Projects/fraudTest.csv")

df.columns = df.columns.str.lower()
df.head(3)

```

### Miscelaneous
* Review the contents of `.gitignore`


<!-- ###################################################################### -->
## First commit on GitHub
* You can either use the VSCode graphical tools or a git commands in a terminal




<!-- ###################################################################### -->
<!-- ###################################################################### -->
# What's next ?
* Go to the directory `./98_EDA` and read the [README.md](./98_EDA/README.md) file 
    * The previous link (``README.md``) may not work on GitHub but it works like a charm locally in VSCode or in a Web browser
    * [Try this](https://github.com/40tude/fraud_detection_2/tree/main/98_EDA)













<!-- 

* This is an updated/reloaded/extended/expanded version of the first version of the [fraud_detection](https://github.com/40tude/fraud_detection) project
 -->


<!-- ###################################################################### -->









<!-- 
## How to use the project ?
1. Once you read the slides `01_getaround_project.pptx`
1. Then you can open and run `02_getaround_treshold.ipynb`
1. Finally open and run `03_getaround_pricing.ipynb`
1. Then go to to the ``./API`` and read the ``readme.md`` to get instructions
1. Do the same thing in the `./dashboard` directory -->








<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- # Objectives -->




<!-- ###################################################################### -->
<!-- 
## Ideas and Open Questions 
1. Create a model to predict fraudulent payment in real-time
    * We have a training dataset
    * At this point the "performances" of the model is **NOT** important
        * A baseline model could even always answering "not fraudulent"
        * First thing first, let's make sure the infra works
    * Can we plug a new model easily ?
        * And make inference with 
    * How do we monitor model accuracy over time ?
    * What about if it drift ? 
        * Again, can we plug a new model easily?
1. Create an infrastructure that ingest real-time payments
    * What if the number of payments is increased by 10x
    * How does the infra scale ?
    * We need to plan to consume data in batches of N transactions to be verified each time.
        * In fact, making predictions one after the other will be very slow.
    * For database saving (Store Data above)
        * Must save all the data received from the Real-time Data producer (this is done via an API)
        * We should add a “prediction” column with the result of the model inference (fraud, not_a_fraud)
        * Plus a “true_value” column to be filled later after verification (if any)
            * Doing so, if some confirmations are done one day
            * Then the additional confirmed record can be added to the initial training set
            * The training dataset can evolve over time
1. Classify each payment ?
1. Send the prediction in real-time to a notification center
    * Send email ? 
-->
