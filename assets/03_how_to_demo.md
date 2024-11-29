<!-- 
Start-Process "chrome.exe" -ArgumentList "https://www.example1.com", "https://www.example2.com", "https://www.example3.com"
Start-Process "chrome.exe" -ArgumentList "--new-window", "https://www.example.com"
-->

# Automated Setup

* WIN + SHIFT + E
* Reach ``fraud_detection_2`` directory
* Open with VSCode
* Open a terminal (CTRL + SIFHT + ù)

```powershell
./assets/setup_demo.ps1
```

# Manual Setup
1. Start Docker

1. Launch pgAdmin 4
    * Open the table
    * Open SQL
    * Paste: `SELECT count(*) FROM fraud_detection_2_table;`
    * If necessary:
        * `SELECT * FROM fraud_detection_2_table;`
        * `SELECT count(*) FROM fraud_detection_2_table;`
        * `SELECT count(*) FROM fraud_detection_2_table WHERE fraud_confirmed IS NULL;`
        * `SELECT count(*) FROM fraud_detection_2_table WHERE fraud_confirmed IS NOT NULL;`
        * `UPDATE fraud_detection_2_table SET fraud_confirmed = NULL;`

1. Open GMail

1. Open Heroku
    * https://dashboard.heroku.com/apps
    * https://fraud-detection-2-ab95815c7127.herokuapp.com/

1. Open AWS
    * https://eu-west-3.console.aws.amazon.com/console/home?region=eu-west-3

1. Open 
    * http://localhost:8080  
    * philippe + ...93#

1. Open Confluent: https://confluent.cloud/home
    * Sign in with Google
    * https://confluent.cloud/environments/env-7q7o7j/clusters/lkc-dpp21o/topics/topic_1/overview
    * https://confluent.cloud/environments/env-7q7o7j/clusters/lkc-dpp21o/topics/topic_2/overview


1. Start Airflow
    * Open a terminal in `01_model_and_data\02_model_and_data_care\01_dag_extract_sql`
    * Run: `docker compose up`
    * http://localhost:8081


1. **Airflow MUST BE UP AND RUNNING**
    * Open a terminal in `01_model_and_data\02_model_and_data_care\01_dag_extract_sql`
    * Run: `docker volume ls`
    * Find: `01_dag_extract_sql_extractor_sql_dag_shared_app`
    ```powershell
    docker run --rm `
      -v C:/Users/phili/OneDrive/Documents/Programmation/fraud_detection_2/01_model_and_data/01_model_and_data_ops/06_extractor_sql_dag/app:/source `
      -v 01_dag_extract_sql_extractor_sql_dag_shared_app:/mnt `
      busybox sh -c "cp -r /source/. /mnt/"

**Airflow MUST BE UP AND RUNNING**
    docker ps -a --format "{{.ID}}:    {{.Names}}"

    # Check 01_dag_extract_sql-airflow-worker-1
    docker exec -it 01_dag_extract_sql-airflow-worker-1 bash
    ls -al /home/app

    # You should see `.env` & `extractor_03.py`
    ```




<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->




# Producer
* Navigate to `./02_business\01_application_ops\01_producer`
    * `cd ./02_business\01_application_ops\01_producer`
* Run:
    * `./build_img.ps1`
    * `./run_app.ps1`
* On Confluent Topic 1, messages should appear (4 per minute)





# Modelizer
* Navigate to `01_model_and_data\01_model_and_data_ops\05_modelizer`
    * `cd ./../../../01_model_and_data\01_model_and_data_ops\05_modelizer`
* Run: `./run_app.ps1`
* Open: http://localhost:8005/
* Copy one of the two suggestions
* Check the documentation using the button
* Execute the command
* Force an error to demonstrate exception handling
* Show retrieval of the version number
* Demonstrate engine switching
* Show version 3
* …
* We MUST close the Modelizer before we move to the Consumer demo
	* Open a new terminal
	* `cd ./01_model_and_data\01_model_and_data_ops\05_modelizer`
	* docker compose down
	* Close the terminal or go back to the previous one.



# Consumer
* Navigate to `02_business\01_application_ops\02_consumer`
    * ``cd ./../../../02_business\01_application_ops\02_consumer`` 
* Run:
    * `./build_img.ps1`
    * `./run_app.ps1`
        * This will start both Modelizer and Consumer
* On Confluent Topic 2, messages should appear (4 per minute)



# Logger SQL + Tests
* Navigate to `02_business\01_application_ops\03_logger_sql_testable`
    * `cd ./../../../02_business\01_application_ops\03_logger_sql_testable`
* In pgAdmin 4:
    * Run: `SELECT count(*) FROM fraud_detection_2_table;`
* Run: `./run_app.ps1`
* Demo mode: it will add only 3 records to the database


## Local Tests
* Delete files in `./test_reports`
* Run: `./test_app.ps1`
* Open `test_reports\pytest_report.html` in a web browser


## Tests in Jenkins
* Go to Jenkins: `localhost:8080`
* Show `fraud_detection_2_tests`
* Explain the container invocation
* Show the script and email sending functionality
* Build now
* View logs
* Check emails and the attachment

# Extract SQL - DAG Airflow
* Navigate to `01_model_and_data\02_model_and_data_care\01_dag_extract_sql`
    * `cd ./../../../01_model_and_data\02_model_and_data_care\01_dag_extract_sql`
* Run: `docker compose up`
* Access Airflow at `localhost:8081`
* ``extractor_sql``
* Explain container invocation within a DAG
* Trigger the DAG
* Show logs
* Go to AWS S3
* Verify the updated `validated.csv`

# Drift Analysis in Jenkins
* Go to Jenkins: `localhost:8080`
* Open the task: `fd2_drift_report_generator`
* Show it is scheduled to run every 4 hours
* Show the script
* Explain container invocation:
    * Run: `docker compose up fd2_drift_generator`
* Build the task
* Check emails
* Follow the link
* Discuss the Heroku web server
* Return to the homepage and show the calendar

# Create a Model Training Image
* Navigate to `01_model_and_data\01_model_and_data_ops\03_docker_images_for_train_code\02_sklearn_trainer`
    * ``cd ./../../../01_model_and_data\01_model_and_data_ops\03_docker_images_for_train_code\02_sklearn_trainer``
* Run: `./build_fraud_trainer.ps1`

# Start Model Training
* Navigate to `01_model_and_data\01_model_and_data_ops\04_train_code\02_sklearn\99_smote_random_forest`
    * `cd ./../../../../01_model_and_data\01_model_and_data_ops\04_train_code\02_sklearn\99_smote_random_forest`
* Run: `./run_training`
* Access MLFlow Tracking Server:
    * https://fraud-detection-2-ab95815c7127.herokuapp.com/
* Show the experiment, run, model, and version
* Display artifacts, tags, etc.










<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->


# Shutdown
Aller dans fraud_detection_2\01_model_and_data\02_model_and_data_care\01_dag_extract_sql
docker compose down

Aller dans fraud_detection_2\02_business\01_application_ops\01_producer
docker compose down

Aller dans fraud_detection_2\02_business\01_application_ops\02_consumer
docker stop consumer modelizer
docker compose down (TO DO : marche pas bien…)



`cd ./../../../../../`

