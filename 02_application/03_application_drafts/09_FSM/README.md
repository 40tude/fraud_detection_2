<!-- ###################################################################### -->
<!-- ###################################################################### -->

# *****  Still under construction *****

# Finite State Machine

* Should run in a Docker an image (fsm.img)
* Use docker compose



# No Docker
* conda create --name fsm_no_docker python=3.12 -y
* aller dans C:\Users\phili\OneDrive\Documents\Programmation\fraud_detection_2\99_tooling\13_FSM\app
* code .
* conda install flask -c conda-forge -y

* Pour lancer la FSM et le controller
* Ouvrir un terminal dans ./app
* Lancer ./run_app.ps1 d'un côté
* Passer sous VSCode
* Ouvrir controler.py
* F5

# With Docker compose
* Bien voir que dans le code de la FSM on lance avec 
app.run(host="0.0.0.0", port=5000)  # in docker
et plus avec
app.run(host="127.0.0.1", port=5000, debug=True)

* Ajouter un port dans docker-compose.yml
* Lancer avec run_app.ps1 (celui qui est au niveau du docker-compose.ymal pas celui qui est dans /app)
* Ouvrir un terminal
* Activer un environnement virtuel qui dispose de requests (conda activate fsm_no_docker par exemple)
* Aller dans ./app
* Mancer python .\controler.py
* Ca tourne on est content


## Regles des ports du docker compose
ports:
      - "5000:5000"  # host:container


Internal port (container): 
This is the port on which your application runs inside the container. 
In your example, this is 5000, meaning that your Flask application, when running inside the container, listens on port 5000.

External (host) port: 
This is the port on which your application will be accessible from outside the container
i.e. from your machine or other machines on the same network. 
In your example, this is also 5000, meaning that you can access, from outside the container, your Flask application via 
    * http://localhost:5000 
    * or http://<ip-address-of-your-machine>:5000 


