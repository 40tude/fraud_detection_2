<!-- 
TODO : La doc pour faire tourner extractor_sql_dag
TODO : Faire un Evidenlty minimal histoire de voir si ça tourne
TODO : Gestion exception dans Fast PI si on passe les mauvais paramètres
TODO : Faire une vidéo
TODO : Faire un meta docker compose à la racine du projet
TODO : Faire un script de démarrage qui utilise le meta docker compose, lance chrome sur Heroku, pgAdmin, Confluent Topic 1 et 2...
TODO : Finir les tests (avec les 2 docker compose) qui sont expliqués dans 99_tooling\25_DinD\README.md
TODO : Dans 08_airflow\README.md, voir si on peut passer une chemin relatif dans 
docker run --rm `
    -v C:/Users/phili/OneDrive/Documents/Programmation/fraud_detection_2/06_extractor_sql_dag/app:/source `
    -v 08_airflow_extractor_sql_dag_shared_app:/mnt `
    busybox sh -c "cp -r /source/. /mnt/"

Trouver des ports
netstat -an | Select-String "LISTENING"

-->

<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Fraud Detection 2 

### JEDHA Bootcamp - AI Architect - RNCP 38 777 - 2024


<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Read the .pptx first
* If and only if you read this ``README.md`` after **Nov 28, 2024**. 
* Otherwise, I'm still working on the project and the slides may not be up to date.
* The content of the slides is mainly a cut-and-paste of what's available in the project notebook(s) and other files
* The idea is that the slides should help you understand the project and its results, guiding you step by step
* [The slides](./assets/01_fraud_detection_2_project.pptx)


<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Video - FR
A 18 minutes long video where I explain (in French) the rationales of the architecture, how it works etc. It is mostly based on the slides. I'm working a second video where I'll show running code.

* [YouTube](https://youtu.be/uJKpLAfofVA) 



<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Read the README.md files in order
* The submodules of the project have their own 
    * directory 
    * ``README.md``
* At the end of each ``README.md`` files there is a **What's next?** section with a link to the next submodule and ``README.md`` file to read.
* Following the flow of the ``README.md`` you should have a better understanding of how the project was designed, the rationales behind some decisions and how the submodules works etc. 
* Otherwise, especially when reading for the first time, you may have difficulty understanding what is happening. For example, if you read the documentation of ``01_model_and_data\01_model_and_data_ops\03_docker_images_for_train_code`` before that of ``01_model_and_data\01_model_and_data_ops\02_mlflow_tracking_server`` you risk asking yourself unnecessary questions in relation to the SQL base, the AWS S3... When in fact everything is explained in the previous ``README.md``.

<!-- ###################################################################### -->
## Some of the README.md you can read

* [Introduction.md](./assets/02_introduction.md) : 

### Model & Data layer
* [01_model_and_data\01_model_and_data_ops\02_mlflow_tracking_server\README.md](./01_model_and_data/01_model_and_data_ops/02_mlflow_tracking_server/README.md) : 
* [01_model_and_data\01_model_and_data_ops\04_train_code\01_minimal\README.md](./01_model_and_data/01_model_and_data_ops/04_train_code/01_minimal/README.md) : 
* [01_model_and_data\01_model_and_data_ops\04_train_code\02_sklearn\01_template\README.md](./01_model_and_data/01_model_and_data_ops/04_train_code/02_sklearn/01_template/README.md) :
* [01_model_and_data\01_model_and_data_ops\05_modelizer\README.md](./01_model_and_data/01_model_and_data_ops/05_modelizer/README.md) : Not yet written
* [01_model_and_data\01_model_and_data_ops\06_extractor_sql\README.md](./01_model_and_data/01_model_and_data_ops/06_extractor_sql/README.md) : Not yet written
* [01_model_and_data\01_model_and_data_ops\06_extractor_sql_dag\README.md](./01_model_and_data/01_model_and_data_ops/06_extractor_sql_dag/README.md) : Not yet written

### Business layer
* [02_business\01_application_ops\01_producer\README.md](./02_business/01_application_ops/01_producer/README.md) :
* [02_business\01_application_ops\02_consumer\README.md](./02_business/01_application_ops/02_consumer/README.md) :
* [02_business\01_application_ops\03_logger_sql\README.md](./02_business/01_application_ops/03_logger_sql/README.md) : Not yest finished

### Test & Monitoring (either Business or Model & Data layer)
* [02_business\01_application_ops\03_logger_sql_testable\README.md](./02_business/01_application_ops/03_logger_sql_testable/README.md) :
* [01_model_and_data\02_model_and_data_care\01_dag_extract_sql\README.md](./01_model_and_data/02_model_and_data_care/01_dag_extract_sql/README.md)


### Draft (either Business or Model & Data layer)
* [02_business\03_application_drafts\11_testing\README.md](./02_business/03_application_drafts/11_testing/README.md) : 
* [02_business\03_application_drafts\14_Jenkins_Testing\README.md](./02_business/03_application_drafts/14_Jenkins_Testing/README.md) : 


<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Directories & files organization

## Content of the directories

### Directories are organized according to the following mental scheme

Where the global application is divided into 2 complementary layers. 

1. **Model and Data Layer**: This refers to the part of the application responsible for the quality and performance of the models and data. Its focus is on developing, training, and optimizing machine learning models, as well as ensuring the data used is clean, well-prepared, and suitable for the task. This layer is detached from business logic and solely concerned with inference quality and model/data integrity. 

1. **Business Layer** : This is the part that utilizes the models produced by the Model and Data Layer. It is not involved in the development of the models but is responsible for their deployment, usability, integration with business applications, and ensuring the overall quality of the user experience. This layer focuses on aligning the technical outputs with business goals and making them accessible and practical for end users. 

<p align="center">
<img src="./assets/img07.png" alt="drawing" width="800"/>
<p>




### The modules are named according the following architecture

You will learn much more about the architecture in [./introduction.md](./introduction.md) but here is how the architecture of the project looks like.  
All the modules (blocks in orange) run in container. This is also true when they are 
* tested (read 02_business\03_application_drafts\14_Jenkins_Testing\README.md) 
* called inside a DAG in airflow (read 01_model_and_data\02_model_and_data_care\01_dag_extract_sql\README.md)

<p align="center">
<img src="./assets/img03.png" alt="drawing" width="800"/>
<p>


Directories are splitted according the 2 layers mentioned before : 
1. `model_and_data` 
1. `business`

Then each of the layers includes only 3 directories : 
1. ``ops`` : where the different modules are stored 
1. `care` : were are stored the CI/CD, monitoring tools
1. `draft` : where are stored the tests, benchmarks and other POC



Directories names start with a double digit numbers (e.g. 03_xxx) which helps understand how the different components of the project are serialized : First the EDA, the set up an MLflow Tracking Server, then build the Docker images where to run the models, then the models... 

```batch
fraud_detection_02

+---01_model_and_data
|   +---01_model_and_data_ops
|   |   +---01_eda
|   |   +---02_mlflow_tracking_server
|   |   +---03_docker_images_for_train_code
|   |   +---04_train_code
|   |   +---05_modelizer
|   |   +---06_extractor_sql
|   |   \---06_extractor_sql_dag
|   +---02_model_and_data_care
|   |   +---01_dag_extract_sql
|   |   \---02_data_drift
|   +---03_model_and_data_drafts
|   |   +---01_client_predict
|   |   +---02_api_test
|   |   +---03_combine_train_and validated
|   |   +---04_map_eda
|   |   +---05_modelizer_no_docker
|   |   +---06_evidently101
|   |   +---07_DinD
|   |   \---08_dag_data_drift
|   \---04_data

+---02_business
|   +---01_application_ops
|   |   +---01_producer
|   |   +---02_consumer
|   |   +---03_logger_sql
|   |   \---03_logger_sql_testable
|   +---02_application_care
|   |   \---01_jenkins
|   \---03_application_drafts
|       +---01_test_kafka_topic1
|       +---02_client_predict_kub
|       +---03_test_compose_topic1
|       +---04_producer_consumer_no_docker
|       +---05_producer_my_docker_img
|       +---06_ez_remote_control
|       +---07_logger_sql
|       +---08_extractor_sql_no_docker
|       +---09_FSM
|       +---10_consumer_modelizer_no_docker
|       +---11_testing
|       |   +---01_my_project
|       |   +---02_my_project
|       |   +---03_greet_docker
|       |   +---03_greet_docker_01
|       |   +---04_greet_docker_smart
|       |   \---05_greet_docker_smarter
|       |       +---app
|       |       +---assets
|       |       +---docker
|       |       +---img
|       |       +---test-reports
|       |       \---tests
|       +---12_dynamic_load
|       |   +---mon_module
|       +---13_resilient_topic
|       \---14_Jenkins_Testing
|           +---app
|           +---docker
|           +---img
|           +---tests
|           \---test_reports
```



### Quick explanation for some of the sub-directories

#### Model-and_data layer
* **02_mlflow_tracking_server** : everything needed to build & deploy mlflow tracking server. Runs in a Docker hosted on Heroku 
* **03_docker_images_for_train_code** : everything needed to build docker images where the models to be trained will run. 
    * **03_docker_images_for_train_code\01_minimal_trainer** : create the image for the minimal trainers  
    * **03_docker_images_for_train_code\02_sklearn_trainer** : create the image for the sklearn trainers 
* **02_train_code** : the models 
    * **04_train_code\01_minimal** : show how, with only 20 lines of code, a trainer can save artifacts, tags, model on MLflow Tracking Server. Runs in a Docker
    * **02_sklearn**
        * **01_template** : serve as a starting point for sklearn models. Based on MLproject. Runs in a Docker container
        * **99_smote_random_forest** : the model used in the project. Based on MLproject. Runs in a Docker container
* **05_modelizer** : Exposes with thru an API the model. Called by the ``consumer`` to get the predictions, rollback model... Runs in a Docker
* **06_extractor_sql** : daily, extracts from the SQL database the confirmed records, fill a ``validated.csv`` on AWS S3. Runs in a Docker
* **06_extractor_sql_dag** : same as above but runs in a Docker container in a Airflow DAQ
* **04_data** : a local copy of the dataset 

#### Business layer
* **01_producer** : read transactions with an API and store them in a Kafka topic (``topic_1``). Runs in a Docker
* **02_consumer** : read transactions from a topic_1, ask for prediction, store the result in a Kafka topic (``topic_2``). Runs in a Docker
* **03_logger_sql** : read (transaction + prediction) from topic_2 and store in SQL database hosted on Heroku. Runs in a Docker
* **03_logger_sql_testable** : Same as above + automatic unit testing with Jenkins. Tests runs in a Docker in a Jenkins Docker container.


* **assets** : Most of the directories have an `assets` folder. They all serve the same purpose. Keep logs, png, csv... And keep the directory clean.






<!-- ###################################################################### -->

## Webliography
* Initial specification : https://app.jedha.co/course/final-projects-l/automatic-fraud-detection-l
* Mlflow Tracking server : https://fraud-detection-2-ab95815c7127.herokuapp.com/
* S3 with training dataset : https://lead-program-assets.s3.eu-west-3.amazonaws.com/M05-Projects/fraudTest.csv
* S3 with additionnal validated data for training : https://fraud-detection-2-bucket.s3.eu-west-3.amazonaws.com/data/validated.csv
* Topics on Confluent : https://confluent.cloud/home
* Previous version of the project (aka Fraud Detection 1): https://github.com/40tude/fraud_detection


<!-- ###################################################################### -->
<!-- ###################################################################### -->
# What's next ?
* Stay in this directory and read the [introduction.md](./introduction.md) file 
    * The previous link (``introduction.md``) may not work on GitHub but it works like a charm locally in VSCode or in a Web browser
    * [Try this](https://github.com/40tude/fraud_detection_2/tree/main/introduction.md)


<!-- ###################################################################### -->
<!-- ###################################################################### -->
# About contributions
This project is developed for personal and educational purposes. Feel free to explore and use it to enhance your own learning in machine learning.

Given the nature of the project, external contributions are not actively sought nor encouraged. However, constructive feedback aimed at improving the project (in terms of speed, accuracy, comprehensiveness, etc.) is welcome. Please note that this project is being created as a hobby and is unlikely to be maintained once my initial goal has been achieved.



<!-- 
Start-Process "chrome.exe" -ArgumentList "https://www.example1.com", "https://www.example2.com", "https://www.example3.com"
Start-Process "chrome.exe" -ArgumentList "--new-window", "https://www.example.com"



-->