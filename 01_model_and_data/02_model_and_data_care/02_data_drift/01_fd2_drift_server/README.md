# Vérifications préliminaires

* Le serveur et le client ont été développés
* On vérifie leur fonctionnement

## Serveur
1. File Exploer
1. Aller dans ./fraud_detection_2/01_model_and_data/02_model_and_data_care/02_data_drift/01_fd2_drift_server
1. Ouvrir un terminal
1. ``conda activate fd2_drift_server_no_docker``
1. ``.\secrets.ps1`` pour ``DRIFT_SERVER_SECRET_KEY`` (``ls env:DR*`` pour vérifier si besoin)
1. ``code .``
1. Ouvrir ``fd2_drift_server.py``
1. F5
1. On peut aller faire un tour sur localhost:5000 (optionnel)

On arrive sur un calendrier qui présente les rapports. On est le 25 novembre. On a pas encore de rapport à cette date.
<p align="center">
<img src="./assets/img01.png" alt="drawing" width="600"/>
<p>

Si on clique sur un jour en particulier on a la liste détaillée des rapports en question. 
<p align="center">
<img src="./assets/img02.png" alt="drawing" width="600"/>
<p>

Si on clique sur un rapport on a le détail.
<p align="center">
<img src="./assets/img03.png" alt="drawing" width="600"/>
<p>


## Client
1. File Exploer
1. Aller dans ``./fraud_detection_2/01_model_and_data/03_model_and_data_drafts/07_evidently_no_docker``
1. Ouvrir un terminal
1. ``conda activate evidently_no_docker``
1. ``.\secrets.ps1`` pour définit les paramètres SMTP (``ls env:SM*`` pour vérifier si besoin)
1. ``code .``
1. Ouvrir ``fd2_drift_report_generator.py``
1. F5
1. Le client s'arrête tout seul

* Du côté du serveur, dans ``./reports`` on doit voir arriver un nouveau rapport (vérifier l'heure dans le nom) 
* On doit aussi recevoir un nouveau mail
* Arrêter le serveur

J'ai reçu un mail. Le titre du rapport précise la date et l'heure (25 novembre, 07H30)

<p align="center">
<img src="./assets/img04.png" alt="drawing" width="600"/>
<p>

Si je clique sur le lien du mail j'arrive sur une page du serveur (qui tourne en local) où je retrouve le rapport mentioné dans le mail. Je peux cliquer sur le lien du rapport de 7H30.

<p align="center">
<img src="./assets/img05.png" alt="drawing" width="600"/>
<p>

Si je retourne sur la page de garde je retrouve le rapport dans le calendrier à la date du 25.

<p align="center">
<img src="./assets/img06.png" alt="drawing" width="600"/>
<p>


Il faut vraiment s'assurer que le client et serveur fonctionnent correctement en local dans 2 instances de VSCode avant de passer à la suite.

On a cette organisation de fichiers côté client
* Ne pas tenir compte des notebook Jupyter, ce sont des tests
* Dans ``requirements.txt``, je prends le temps de lister les differents modules que j'ai installé pour faire tourner le client (evidenlty, pandas...)
* `./reports` c'est une copie des rapports .htmls qui ont été envoyés au serveur

<p align="center">
<img src="./assets/img07.png" alt="drawing" width="400"/>
<p>

Et cette organisation de fichiers côté serveur
* `reports.db` c'est une base SQLite avec la liste des rapports
* `./templates` contient les templates des pages ``.html`` à afficher
* `./reports` contient les rapports reçus
* Ne pas tenir compte de `./assets`, ce repertoire contient par exemple les copies d'écran de ce ``README.md``

<p align="center">
<img src="./assets/img08.png" alt="drawing" width="400"/>
<p>








# Le programme à venir

## Serveur

1. Il tourne en local dans VSCode 
    * Plus facile pour le développement et la mise au point
    * Il recoit des rapports et les présente dans un calendrirer
1. Il faut déployer le serveur sur Heroku (ou une autre plateforme)
    * Il faudra alors faire un test avec le client en local

## Client

1. Il tourne en local
    * Plus facile pour le développement et la mise au point
    * Il réalise une analyse de drift, envoie un mail et fait pervenir le rapport au serveur le cas échéant 
1. Il faut le faire tourner dans un conteneur Docker
    * Le tester en local dans son container Docker
1. On pourra ensuite faire tourner le client dans son conteneur Docker au sein d'un DAG où d'une tache programmée Jenkins
    * On a déjà fait ça avec ``extract_sql``. 
    * Voir : ``01_model_and_data\02_model_and_data_care\01_dag_extract_sql\README.md``   




# Déployer le serveur sur Heroku

* Fermez l'instance de VSCode dans laquelle tournait le serveur
* Avec File Explorer allez à la racine de `fraude_detection_2` (il va falloir pousser sur GitHub)
* Ouvrez avec Code
* Dans la barre de gauche, ouvrez ``01_model_and_data\02_model_and_data_care\02_data_drift\01_fd2_drift_server``
* Ouvrez un terminal intégré dans ce répertoire


``pip list --format=freeze > requirements.txt``
* At the end of requirements.txt add the line "gunicorn==23.0.0"
    * I have to do that because I run WIN11 and I can't install gunicorn
    * gunicorn is only used in "production" on heroku

```txt
blinker==1.9.0
click==8.1.7
colorama==0.4.6
Flask==3.1.0
importlib_metadata==8.5.0
itsdangerous==2.2.0
Jinja2==3.1.4
MarkupSafe==3.0.2
pip==24.2
setuptools==75.1.0
Werkzeug==3.1.3
wheel==0.44.0
zipp==3.21.0
gunicorn==23.0.0
```

Create file ``Procfile``
* Pay attention to :  fd2-drift-server:create_app()
* name of the Python file + ":" + entry_point()
* in fd2-drift-server.py take a look at create_app()
    * Gunicorn uses the create_app() function to obtain the Flask application instance, and starts the WSGI server

```
web: gunicorn --workers=3 'fd2-drift-server:create_app()'
```


Create file ``runtime.txt``

```
python-3.12.7
```


Create file ``.slugignore`` file
```
README.md
assets/
```


### ATTENTION
* Heroku does not allow "_" in project name
* Use "-" to name your project instead



# Migration du client dans un conteneur











# Note
* I use WIN11 (while Heroku runs Linux) but most of the information are platform independent
* I use conda

# How to
You should have all the files already. The lines below explain how the project was initially set up.
* conda create --name fd2-drift-server python=3.12 -y
* conda activate fd2-drift-server
* create directory fd2-drift-server 
* cd ./fd2-drift-server 
* code .
* create file mypy.ini
* create file fd2-drift-server.py
* conda install flask mypy markdown pygments -y
* create a secrets.ps1 similar to

```
$env:FLASHCARDS_SECRET_KEY = "blablabla"
```
* create .gitignore
    * at least, add a line with : secrets.ps1
* Open a terminal in VSCode (CTRL + ù)
    * ./secrets.ps1
* Strike F5 in VScode
    * The app should be running locally
    * CTRL+C
* conda list -e > ./assets/requirements_conda.txt
* pip list --format=freeze > requirements.txt
    * At the end of requirements.txt manually add the line "gunicorn==23.0.0"
    * I have to do that because I run WIN11 and I can't install gunicorn
    * gunicorn is only used in "production" on heroku
    * If you run Linux
        * conda install gunicorn -y
        * pip list --format=freeze > requirements.txt
* create file Procfile
    * Pay attention to :  fd2-drift-server:create_app()
    * name of the Python file + ":" + entry_point()
    * in fd2-drift-server.py take a look at create_app()
        * Gunicorn uses the create_app() function to obtain the Flask application instance, and starts the WSGI server
* create file runtime.txt
* From VSCode commit to github
* From the VSCode integrated terminal 


* Open a terminal
    * Make sure you are **AT THE ROOT** of the `fraud-detection-2` project directory

    ```
    heroku login
    heroku create fraud-detection-2       # '-' NOT '_' since Heroku does not allow '_'
    ```
    * Pay attention to the content of the terminal and note that these 2 urls have been created 
        * https://fraud-detection-2-ab95815c7127.herokuapp.com/ 
        * https://git.heroku.com/fraud-detection-2.git
    
    * Push the changes in the project ``fraud_detection_2`` to GitHub
    * Now with the 2 lines below we :
        1. add Heroku as a remote  
        1. push the sub-directory `./00_mlflow_tracking_server` to Heroku 

    ```
    git remote add heroku https://git.heroku.com/fraud-detection-2.git
    git subtree push --prefix 00_mlflow_tracking_server heroku main
    ```





    * heroku login
    * heroku create fd2-drift-server
        * https://fd2-drift-server-41b349ab0591.herokuapp.com/ 
        * https://git.heroku.com/fd2-drift-server.git
        * are created for example
    * git remote add heroku https://git.heroku.com/fd2-drift-server.git
    * git push heroku main
    * heroku config:set FLASK_ENV=production
    * heroku config:set FLASHCARDS_SECRET_KEY=blablabla 
    * heroku open
    * This should work

# Workflow
## To run locally
* Open a terminal in VSCode and run ``./secrets.ps1`` once
    * You can type ``ls env:FLASH*`` to double check
* Modify files etc.
* Optional - Commit on github from VSCode    
* Strike F5 while ``fd2-drift-server.py`` is open
    * If the app complains
        1. Stop the app (CTRL+C)
        1. The Python Debug Console should be opened
        1. Run ``./secrets.ps1`` once in the Python Debug Console

## To deploy on Heroku
* Modify files etc.
* Commit on github from VSCode    
* ``git push heroku main``
* type ``heroku open`` in the terminal (or visit the app web page)

# Q&A

---
* Q : How to check gunicorn is serving the app on Heroku?
* A : Open a terminal locally
    * heroku logs --tail
    * CTRL+C 
    * CTRL+F gunicorn
    * You should see a line similar to : `[INFO] Starting gunicorn 23.0.0`

---
* Q : Can I organize the markdown files in directories and sub-directories ?
* A : Yes as long as they are under the ``./static/md`` directory 

---
* Q : Can I organize the .png cards in directories and sub-directories ?
* A : Yes as long as they are under the ``./static/png`` directory 

---
* Q : Can I insert a link to a .png file or a link to a web page into the answer ?
* A : Yes. Answers are plain markdown files so you can insert 
    * link to images
    * source code
    * bold, italic fonts
    * equations and math symbols (Latex syntax)


---
* Q : The answer includes a link to a ``.png`` file. What is the path I should use in the content of the answer ? 
* A : Let's take an example :
    1. Your markdown file (which includes one or more set of question/answer) is in ``.\static\md\dummy_test`` directory
    1. The name of the markdown file is ``dummy.md``
    1. Underneath ``dummy.md`` there is an ``assets`` where there is `dummy.png`
    
To make it clear, so far, the organization of the files looks like :

```
./md
│   other_QA_file_01.md
│   other_QA_file_02.md
│
└───dummy_test
    │   dummy.md
    │
    └───assets
            dummy.png
```

Here is how to point the ``./md/dummy_test/assets/dummy.png`` from the file ``./md/dummy_test/dummy.md``.

```
Question : The question I want to ask

Answer  : 
This is the expected answer with a link to the ``./assets/dummy.png`` 


<p align="center">
<img src="../static/md/dummy_test/assets/dummy.png" alt="dummy" width="577"/>
</p>

```
* Keep in mind you **MUST** point the ``dummy.png`` as if you were in ``./templates/index.html``
* Indeed the markdown text of the questions and answers is inserted into the ``index.html``
 


# About contributions
This project was developed for personal and educational purposes. Feel free to explore and use it to enhance your own learning in machine learning.

Given the nature of the project, external contributions are not actively sought or encouraged. However, constructive feedback aimed at improving the project (in terms of speed, accuracy, comprehensiveness, etc.) is welcome. Please note that this project was created as part of a certification process, and it is unlikely to be maintained after the final presentation.    
