<!-- 

# Can be useful in pgAdmin
# select count(*) FROM fraud_detection_2_table;
# select count(*) FROM fraud_detection_2_table where fraud_confirmed is null;
# select count(*) FROM fraud_detection_2_table where fraud_confirmed is not null;
# UPDATE fraud_detection_2_table SET fraud_confirmed = NULL; 


docker compose up --exit-code-from extractor_sql
-->


<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Objectif
Je développe sous WIN11.
Dans le cadre du projet ``fraud_detection_2``, je souhaite utiliser Airflow et ses DAG.
Dans mon cas, ces derniers sont des conteneurs dans lesquels s'exécute tel ou tel module du projet.
Oui, je confirme cela veut dire qu'au sein du conteneur Airflow, on va exécuter des conteneurs.
C'est du Docker In Docker (DinD).
Il y a un module par conteneur et ça tombe bien car chaque module a été conçu pour ne fonctionner que dans un conteneur.
Quand je dis module c'est par exemple : ``extractor_sql``, ``logger_sql``...


<!-- ###################################################################### -->
<!-- ###################################################################### -->
## Pourquoi des conteneurs dans des DAG ?
Si le DAG est un code Python qui utilise telle ou telle bibliothèque, il faut que cette dernière soit installée dans le conteneur où s'exécute Airflow.
Si demain des modules nécessitent Pytorch, Tensorflow, Pandas...
Il faudra que toutes ces biblitohèques soient disponibles dans le conteneur de Airflow.
On va vite rencontrer des problèmes de versions, d'incompatibilités (ce n'est pas pour rien que les environnements virtuels ont été inventés).
De plus, faire tourner du code dans des conteneurs dans des DAG permet de bien séparer les responsabilités.
Airflow orchestre des DAG, il ne s'occupe pas et il n'est pas impacté par ce qui est fait dans les DAG.
Dans le DAG, le code qui tourne dans le conteneur a préalablement été validé testé... 
Il dispose des librairies dont il a besoin et il n'a même pas conscience qu'il s'exécute dans un DAG. Il fait sont job comme avant.


<!-- ###################################################################### -->
<!-- ###################################################################### -->
## Limitations et avantages des DinD
Les arguments/contre-arguments que l'on peut lire à droite et à gauche sont généralement les suivants.


<!-- ###################################################################### -->
### Limitations
* Complexité : Ajoute un niveau supplémentaire d’abstraction qui peut compliquer le débogage. Je confirme.
* Impact sur la performance : Les conteneurs exécutés par un conteneur DinD sont emboîtés, ce qui peut entraîner une surcharge de ressources. Pas vraiment un problème. Y a qu'à ajouter des processeurs.
* Sécurité : Les conteneurs exécutés dans un environnement DinD **partagent le noyau du conteneur parent**, ce qui peut poser des problèmes de sécurité si l'isolation n'est pas bien gérée.
Volumes et réseaux : Gérer les volumes et les réseaux entre les couches DinD peut être fastidieux. Oui je confirme c'est une galère si on a pas les idées claires.

<!-- ###################################################################### -->
### Avantages
 * Isolation : Permet un cloisonnement total entre l’environnement Docker utilisé dans le conteneur et le moteur Docker de l’hôte. C'est justement ce que je cherche.
* Portabilité : Les configurations peuvent être packagées dans une image, ce qui facilite leur transport et leur partage. Ca fait partie du cahier des charge car rien ne m'assure qu'à terme les modules seront toujours testés puis exécutés dans leur environnement de départ.
* Facilité de configuration dans les pipelines CI/CD : Pas besoin de dépendre d’un démon Docker externe. Tout est encapsulé dans un conteneur.
* Flexibilité : Possibilité d’exécuter différentes versions de Docker dans différents conteneurs.



<!-- ###################################################################### -->
<!-- ###################################################################### -->
## Pourquoi faire ces tests ?
Je rencontre actuellement de gros problèmes avec Airflow. Cela concerne entre autres :
1. Le passage des variables d'environnement (typiquement des credentials) du système hôte WIN11 au conteneur Airflow puis du conteneur Airflow au conteneur où s'exécute le module.
1. Le mapping de volume entre le système hôte WIN11 et le conteneur Airflow puis entre le conteneur Airflow et conteneur où s'exécute le module


<!-- ###################################################################### -->
<!-- ###################################################################### -->
## Quel est le programme ?
Afin de circonscrire les problèmes je vais sortir Airflow de l'équation.
Je vais utiliser un module qui a été testé en long en large et en travers et dont on sait qu'il fonctionne (``extractor_sql``).
Ce dernier va chercher des enregistrements dans une base de données PostgreSQL hébergée sur Heroku. Il dépose ensuite ces enregistrments dans un fichier ``.csv`` sur un bucket S3 d'AWS.
Le module nécessite des credentials pour se connecter à Heroku et AWS.
Pour construire le module il suffit d'invoquer ``docker compose`` à la racine du répertoire où est le module.
Je sais que la méthode fonctionne et je sais que le module fonctionne.
Si il y a des problèmes à résoudre je sais donc qu'il ne viendront pas de là.



<!-- ###################################################################### -->
### Le programmme
1. On va construire une image qui aura la capacité de faire du DinD 
1. À partir de cette image, on va instancier un conteneur puis se connecter dessus
1. Une fois dans le conteneur, on va contruire l'image nécessaire à l'exécution du module. Normalement, on ne doit pas changer la ligne de commande qu'on utilise déjà.
1. À partir de cette seconde image, on va instancier un conteneur et y exécuter le module. Là aussi, cela ne doit pas changer ce que l'on fait d'habitude.
1. Le conteneur doit monter en mémoire et le code du module doit démarrer. À la fin, un nouveau fichier ``.csv`` doit arriver sur le bucket S3 et le second conteneur doit s'éteindre.







<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Création de l'image

* S'assurer que le port 2375 est ouvert sur Docker

<p align="center">
<img src="./assets/img00.png" alt="drawing" width="600"/>
<p>


Créer un Dockerfile pour construire une image dans laquelle on va pouvoir faire du DinD
* Noter qu'à la fin on précise le répertoire courant 
* Et qu'on copie depuis Win11, le contenu du sous-répertoire ``./hosted`` vers le répertoire `/home/hosted`
* Le répertoire ``./hosted`` est une copie du répertoire du module `extractor_sql`

```dockerfile
# Dockerfile

# Base image
FROM python:3.12-slim

# Install prerequisites and Docker
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for Docker in Docker
ENV DOCKER_HOST=unix:///var/run/docker.sock
ENV DOCKER_TLS_CERTDIR=""

# Set working directory
WORKDIR /home/hosted
COPY ./hosted /home/hosted

# Expose Docker socket (optional, for debugging)
EXPOSE 2375

# Default command
CMD ["/bin/bash"]
```

Créer un script pour construire l'image 


```powershell
# build_host.ps1

docker build -t python-dind:3.12-slim .
```

Ouvrir un terminal et y lancer le script. À la fin on retrouve une nouvelle image ``python-dind`` dont la version est ``3.12-slim``

```powershell
./build_host.ps1
```

<p align="center">
<img src="./assets/img01.png" alt="drawing" width="600"/>
<p>



Créer un script pour lancer une instance de l'image du premier host
* ``--privileged`` est nécessaire pour que le conteneur puisse gérer Docker
* Faire attention au `//` devant le `var`
* Cette ligne donne accès au démon Docker de l’hôte.
* Le second mapping partage le répertoire local ``./hosted`` avec un répertoire `./home/hosted` dans le conteneur
* C'est bien `${pwd}` avec des accolades et pas autre chose qu'il faut utiliser
* En cas de problème il faut vérifier qu'il n'y a pas d'espace après les backticks en fin de ligne

```powershell
# run_host.ps1

docker run -it --rm --privileged `
    -v //var/run/docker.sock:/var/run/docker.sock `
    -v ${pwd}/hosted:/home/hosted `
    python-dind:3.12-slim
```

Lancer une instance de l'image dans un conteneur
* On se retrouve dans le répertoire courant précisé dans le Dockerfile (``/home/hosted``)
* Comprendre que ce répertoire n'est **PAS** une copie mais un mapping du répertoire ``./hosted`` de l'hôte WIN11
* Si on crée un fichier (`touch zoubida.txt`) dans le conteneur on le voit apparaître sous WIN11 et vice versa.

```powershell
./run_host.ps1
```
<p align="center">
<img src="./assets/img02.png" alt="drawing" width="600"/>
<p>



<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Executer le module dans son conteneur

* On était sous WIN11
* On a démarré un conteneur dans lequel on peut faire du DinD
* On est maintenant dans un répertoire (``/home/hosted``) où on retrouve les fichiers du module
    * Entre autres son ``docker-compose.yml``
    * Les répertoires ``app`` et ``docker`` qui contiennent respectivement le code du module et les instructions pour construire l'image qui servira à créer les conteneur dans lesquelle l'application s'executera.
    * Il faut noter qu'il y a un fichier ``./app/.env`` qui contient les credentials pour se connecter à AWS et à la base SQL. Si ce fichier n'est pas là parce que vous avez récupéré le projet depuis GitHUb faut le recréer.

Contrairement à d'autres ``README.md`` du projet `fraud_detection_2`, je vais commencer par montrer le résultat final puis on ira ensuite analyser les différents fichiers de configuration pour comprendre pourquoi ça marche. Oui, oui j'assume, c'est un "teaser".

Au prompt du conteneur qu'on vient de lancer on va saisir cette ligne de commande
* Bien voir que c'est ``docker compose`` et pas ``docker-compose`` (ancienne version et syntaxe à ne plus utiliser)
* Le `--exit-code-from` permet d'arrêter le conteneur quand `extractor_sql` sera terminé

```bash
docker compose up --exit-code-from extractor_sql
```

<!-- ###################################################################### -->
<!-- ###################################################################### -->
## Explications des logs
1. En jaune, l'image `extractor_sql_dag_img` n'est pas disponible donc faut la construire
1. En bleu, on passe par toutes les couches de construction de l'image
1. Après en blanc, on crée 2 conteneurs `extractor_sql_dag` et `first_container` qui sont liés l'un à l'autre
1. Le code qui est dans `extractor_sql_dag` démarre
    * Il se connecte à la base de données, il trouve une table...
    * À la fin il nous dit que le jeu de données validées contient 1 observation (pour les besoins de la cause, j'ai pris soin de vider le fichier ``validated.csv`` qui est sur le bucket S3)
1. Le code se termine
1. Les 2 conteneurs s'eteignent
1. On est revenu au prompte de départ



Voilà ce que je vois à l'écran

<p align="center">
<img src="./assets/img03.png" alt="drawing" width="600"/>
<p>



Si on relance la même commande, on va faire l'économie de la construction de l'image
* Comme le code du module est en mode ``DEMO_MODE`` et ``DEBUG_MODE`` le module n'envoie qu'un enregistrement validé à la fois dans le fichier ``.csv``
* Ce dernier contient maintenant 2 enregistrements
* Si besoin il faut lire les lignes 26 et 29 du ``./hosted/app/extractor_03.py``

```bash
docker compose up --exit-code-from extractor_sql
```

<p align="center">
<img src="./assets/img04.png" alt="drawing" width="600"/>
<p>



<!-- ###################################################################### -->
<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Explication de la configuration



<!-- ###################################################################### -->
<!-- ###################################################################### -->
## Fichier ``docker-compose`` 

On parle du fichier ``./hosted/docker-compose``

```yaml
# docker-compose 

services:

  extractor_sql:
    image: extractor_sql_dag_img
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: extractor_sql_dag
    env_file:  
      - ./app/.env
    volumes:
      - extractor_sql_dag_shared_app:/home/app        # What is mounted : local directory
    working_dir: /home/app
    command: python extractor_03.py  
    restart: "no"                                     # Make sure the container do not restart automatically

  first_container:
    image: busybox:latest
    container_name: first_container
    volumes:
      - extractor_sql_dag_shared_app:/home/hosted/app # What is mounted : local directory
    command: tail -f /dev/null                        # keep the container active while the other container is running
    depends_on:
      - extractor_sql                                 # Ensures only that first_container starts after extractor_sql            
    restart: "no"                                     # Make sure the container do not restart automatically

volumes:
  extractor_sql_dag_shared_app:
```


<!-- ###################################################################### -->
### Section ``extractor_sql:``
* Le conteneur s'appuie sur l'image `extractor_sql_dag_img`
* Si cette dernière n'existe pas, il faut la construire en suivant les instructions de la section `build:`
* **IMPORTANT**, avec ``context:`` on précise quel est le répertoire de référence à utiliser à partir de maintenant
    * Avec `.`, on pointe donc sur `/home/hosted/` puisque c'est de là qu'on a invoqué `docker compose up...`
* Ensuite, toujours dans la section `build`, on précise que les instructions à suivre sont dans le fichier `Dockerfile` qui est dans ``./docker`` (on voit ça dans 2 minutes)
* Quand l'image aura été construite, le conteneur s'appelera `extractor_sql_dag` 
    * Faut pas oublier qu'à terme, ce conteneur sera dans un DAG Airflow
* La section ``env_file:`` permet d'indiquer qu'il faut aller chercher des variables d'environnement et les passer au conteneur
    * On utilise le répertoire pointé par ``context:`` comme référence. Donc on indique que le fichier ``.env`` est dans le sous-répertoire ``./app``
* **TRES IMPORTANT**, dans la section ``volumes:`` on précise qu'il faut mapper le volume `extractor_sql_dag_shared_app` au répertoire `/home/app` du conteneur 
    * On voit cette histoire de ``volumes:`` dans 1 minute.
    * Pour l'instant faut imaginer qu'un "répertoire" `extractor_sql_dag_shared_app` sera projeté dans le répertoire `/home/app`
    * Ce que l'on souhaite bien sûr, c'est y retrouver le code du module qui pour l'instant est sur ``./hosted/app`` mais sur WIN11
* Quand tout est en place on précise quel sera le répertoire de référence dans le conteneur
    * Faut comprendre ça comme un `cd /home/app`
* Comme on est, du point de vue du conteneur, dans le répertoire `/home/app` et que Python est dans le path, la commande pour lancer le module est simple (`python extractor_03.py`)
* On indique enfin que le conteneur ne redemarera pas en cas de problème ou autre. Normalement c'est inutile car c'est le comportement par défaut mais ça ne fait pas de mal que de préciser le comportement attendu



<!-- ###################################################################### -->
### Section ``first_container:``
On va décomposer ça en 2 parties.

#### Partie facile
* En gros ce sont toutes les lignes sauf la section `volumes:`
* Il n'y a aucune surprise
* À l'avant dernière ligne, dans la section `depends on:`, on s'assure que les conteneurs démarrent dans le bon ordre
* La commande `tail -f /dev/null` est juste là pour tenir éveillé le ``first_container``. Pas de panique, ça mobilise très peu le processeur. En plus c'est court et ça permet d'arrêter le conteneur ``first_container``quand le conteneur  dont il dépend (``extractor_sql``) s'arrête. On en reparle dans "Partie..."
* La raison pour laquelle on utilise une image ``busybox`` plutôt qu'une autre c'est tout simplement la taille 

<p align="center">
<img src="./assets/img05.png" alt="drawing" width="600"/>
<p>


#### La partie...
* C'est là où on parle des ``volumes:``
* Je trouve que c'est un peu bizarre comme méthode mais bon... 
* **LE** premier truc qu'il faut comprendre, c'est que Docker ne "chaîne" pas les volumes d’un conteneur à l’autre par défaut. Donc, ce n'est pas parce que le sous-répertoire ``./hosted`` sous WIN11 est mappé avec le répertoire local ``/home/hosted`` qu'il sera mappé ou même mappable (je sais plus trop mais je crois que j'ai eu des problèmes)
    * Voir le `-v ${pwd}/hosted:/home/hosted` de la commande ``docker run...`` dans ``run_host.ps1``
* Comme à chaque fois qu'on a un problème en informatique, **LA** solution passe par l'ajout d'un niveau d'indirection
* Ici cela se traduit par la création d'un volume Docker nommé (`extractor_sql_dag_shared_app`)
    * Le nom est à rallonge car je veux être sûr de ne pas le confondre avec un autre
    * Pour simplifier il faut imaginer que c'est un disque partagé dans lequel `first_container` et `extractor_sql_dag` vont avoir accès
* Du coup si on dit que du côté du conteneur `first_container` on mappe le contenu de `/home/hosted/app` sur ``extractor_sql_dag_shared_app``
* On devrait retrouver dans ``extractor_sql_dag_shared_app`` le contenu de ``./hosted`` côté WIN11 car on a lancé le premier conteneur (`docker run...`) avec l'option ``${pwd}/hosted:/home/hosted``
* Finalement si côté du conteneur `extractor_sql_dag` on mappe le contenu de `/home/app` avec ``extractor_sql_dag_shared_app``
* On devrait, par transition, retrouver dans ``/home/app`` le contenu de ``./hosted`` qui est du côté de WIN11
* Pour le coup, on comprend les lignes :
    1. `- extractor_sql_dag_shared_app:/home/app`
    1. `- extractor_sql_dag_shared_app:/home/hosted/app`
    1. `extractor_sql_dag_shared_app:`
* La dernière ligne ci-dessus s'assure, dans le docker-compose que le volume nommé est créé si il n'existe pas.      

La graphe ci-dessous explique comment le contenu de ``WIN11/hosted/app`` se retrouve dans ``extractor_sql_dag/home/app``. En effet `first_container` recoit de la part de WIN11 tout le contenu de ``./hosted`` mais qu'il n'en partage qu'une partie (``./hosted/app``) avec `extractor_sql_dag`. Mais bon du coup `extractor_sql_dag` à accès au ``.py`` et ``.env``.

<p align="center">
<img src="./assets/img06.png" alt="drawing" width="600"/>
<p>


Bon ben voilà, c'est bon, on a tout comprs, c'est terminé. **Oui mais non...**

* **LE** second truc c'est que même si on parle de Docker in Docker, ce qu'il faut comprendre c'est que Docker est conçu pour exécuter des applications ou des processus en tant que services dans des conteneurs. Si aucun processus ne reste actif, le conteneur s’arrête. 
* Ici, même si le conteneur ``extractor_sql_dag`` dépend du volume partagé avec le conteneur `first_container`, cela ne maintient pas le conteneur `first_container` actif pour autant. 
* Docker ne considère pas en effet le partage de volume comme un "processus" qui empêche l'arrêt du conteneur `first_container`.
* Du coup on comprend pourquoi il y a une ligne `command: tail -f /dev/null`. Elle est là pour tenir le premier conteneur éveillé. Ainsi il continue à mapper le volume nommé qui permet au second conteneur d'avoir accès aux credentials (``.env``) et au source du module (``extractor_03.py``) 

Pour finir, et c'est pour ça que cette solution me paraît curieuse, ce qu'il faut comprendre c'est l'enchainement des évènements
1. Je suis sous WIN11
    * J'ai un sous répertoire ``./hosted`` qui comprends un sous répertoire `./app` avec le code du module à lancer
1. Je lance un conteneur 
    * Il mappe le répertoire Windows ``./hosted`` (la source) avec son répertoire local ``/home/hosted`` (la cible)
1. Au prompt Linux, avec un ``docker compose up`` je lance 2 conteneurs : 
    1. ``first_container``   : qui mappe le volume ``extractor_sql_dag_shared_app`` avec son répertoire local ``/home/hosted/app`` 
    1. ``extractor_sql_dag`` : qui mappe le volume ``extractor_sql_dag_shared_app`` avec son répertoire local ``/home/app`` (la cible)
1. Mais comme la mapping opéré par ``first_container`` ne durera que le temps de ``first_container``, on occupe ce dernier en lui faisant envoyer des log du ``/dev/null``. Ca fait penser un peu à la logique des Shadocks. 


##### Note
Pour ceux qui sont curieux... Dans les commentaires de ce ``README.md``, à ce niveau là du document, j'ai laissé un ``TODO``. L'idée c'est de voir si il n'est pas possible de simplifier encore les choses en utilisant 2 ``docker-compose.yaml`` etc. J'ai fait 2 essais et je suis revenu à la rédaction de ce document. Je n'ai pas le temps mais je pense qu'il y a quelque chose à affiner car cela permettrait de s'affranchir du service `first_container`.

<!-- 
## TODO
* Faire un test avec un truc où on utilise 2 docker-compose et où dans le premier on créé extractor_sql_dag_shared_app_2
* On lance le 1er conteneur avec un docker compose car il permet de créer un volume nommé
    * docker compose run dind_service

```yaml
# docker-compose

services:
  dind_service:
    image: python-dind:3.12-slim
    container_name: dind_service
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - extractor_sql_dag_shared_app_2:/home/hosted
    privileged: true
    command: /bin/sh
    stdin_open: true
    tty: true                           # désactive le mode de détachement 

volumes:
  extractor_sql_dag_shared_app_2:
```

* Ensuite pour le second conteneur 
* Faire un nouveau docker-compose où on vire toute la section ``first_container:`` 


```yaml
# docker-compose 

services:
  
  extractor_sql:
    image: extractor_sql_dag_img
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: extractor_sql_dag
    env_file:  
      - ./app/.env
    volumes:
      - extractor_sql_dag_shared_app:/home/app
    working_dir: /home/app
    command: python extractor_03.py  
    restart: "no"                   # Make sure the container do not restart automatically

volumes:
  extractor_sql_dag_shared_app:
```

 -->





<!-- ###################################################################### -->
<!-- ###################################################################### -->
## Le fichier Dockerfile

On parle du fichier ``./hosted/docker/Dockerfile``

```dockerfile
# Dockerfile

FROM python:3.12-slim

# Le répertoire de travail à l'intérieur du conteneur Docker
# defines the current working directory for all subsequent instructions in the 
# Dockerfile (RUN, COPY...), as well as for the execution of commands in the resulting container
WORKDIR /home/app

# requirements.txt will be in /home/app/requirements.txt (not a big deal)
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt    

# copy the content of /app from the host to the current directory (WORKDIR) 
COPY app/ .
```

Il n'y a vraiment rien de particulier à dire c'est vraiment classique de chez classique

<!-- ###################################################################### -->
### Le fichier requirements.txt

On parle du fichier ``./hosted/docker/requirements.txt``

```python
# requirements. txt

psycopg2-binary
sqlalchemy
pandas
fsspec              # for pandas to write/read s3://fraud-detection-2-bucket
s3fs                # for pandas to write/read s3://fraud-detection-2-bucket
```

Là aussi aucun changement. On fait juste la liste des modules nécessaires à l'execution de `extractor_03.py`.
L'interêt majeur c'est que cette configuration logicielle n'impact pas du tout le contexte logiciel dans lequel s'exécute Airflow.


<!-- ###################################################################### -->
<!-- ###################################################################### -->
# Conclusion
* Je pense qu'on est prêt pour revenir vers Airflow



<!-- ###################################################################### -->
<!-- ###################################################################### -->
# What's next ?
* Go to the directory `./08_airflow` and read the [README.md](../../08_airflow/README.md) file 
* The previous link (``README.md``) may not work on GitHub but it works like a charm locally in VSCode or in a Web browser
* [Try this](https://github.com/40tude/fraud_detection_2/tree/main/08_airflow)
