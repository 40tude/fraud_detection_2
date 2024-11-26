

<!-- 
netstat -an | Select-String "LISTENING"
 -->

# A garder en tête
* conda activate modelizer_no_docker pour debug etc.
* ou lancer dans container 

# Mise à jour de la configuration 20 11 2024
* supprimer secrets.ps1 et passer en .env
* Dans docker-compose 
    Remplacer
    environment:
        - AWS_REGION=${AWS_REGION}  
        - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}  
        - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    Par
    env_file:  
        - ./app/.env

* Mettre à jour la section build

    build: 
        context: .
        dockerfile: /docker/Dockerfile

* Mettre à jour le run_app.ps1
docker compose up

* Modifier modelizer03.py
from dotenv import load_dotenv

* 

# -----------------------------------------------------------------------------
load_dotenv()
latest_mod, previous_mod = get_models()
current_mod = latest_mod
app = FastAPI()
...


* Ajouter  à requirements.txt    
    * python-dotenv
    * jinja2


* Much better looking home page
    * Use bootstrap and Jinja2

<!-- ###################################################################### -->
<!-- ###################################################################### -->
# What's next ?
<!-- * Go to the directory `./98_EDA` and read the [README.md](./98_EDA/README.md) file  -->
    * The previous link (``README.md``) may not work on GitHub but it works like a charm locally in VSCode or in a Web browser
    <!-- * [Try this](https://github.com/40tude/fraud_detection_2/tree/main/98_EDA) -->
