import requests

url = "http://127.0.0.1:5000/update"
new_value = 10
response = requests.post(url, json={"new_value": new_value})

if response.status_code == 200:
    print("Valeur mise à jour avec succès:", response.json())
else:
    print("Échec de la mise à jour:", response.status_code, response.text)
