# setup_demo.ps1

$DockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Start-Process -FilePath $DockerPath 


$pgAdminPath = "C:\Users\phili\AppData\Local\Programs\pgAdmin 4\runtime\pgAdmin4.exe"
Start-Process -FilePath $pgAdminPath 


$urls = @(
    "http://localhost:8080",
    "http://localhost:8081",
    "https://mail.google.com/mail/u/0/?hl=fr#inbox",
    "https://confluent.cloud/environments/env-7q7o7j/clusters/lkc-dpp21o/topics/topic_1/message-viewer", 
    "https://confluent.cloud/environments/env-7q7o7j/clusters/lkc-dpp21o/topics/topic_2/message-viewer",
    "https://eu-west-3.console.aws.amazon.com/console/home?region=eu-west-3", 
    "https://dashboard.heroku.com/apps", 
    "https://fraud-detection-2-ab95815c7127.herokuapp.com/"
)
$params = @("--new-window")
$params += $urls
Start-Process msedge.exe -ArgumentList $params


# Chemin vers le répertoire contenant le fichier docker-compose.yml
$AirflowPath = "C:\Users\phili\OneDrive\Documents\Programmation\fraud_detection_2\01_model_and_data\02_model_and_data_care\01_dag_extract_sql"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd `"$AirflowPath`" && docker compose up" -NoNewWindow -Wait

