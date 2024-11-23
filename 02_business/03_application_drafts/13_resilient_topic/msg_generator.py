import json
import random
import string


# -----------------------------------------------------------------------------
# Génère un ID aléatoire sur 12 chiffres, séparés en segments de 4 chiffres
def generate_random_id():
    return "-".join(f"{random.randint(0, 9999):04}" for _ in range(3))


# -----------------------------------------------------------------------------
# Génère une chaîne de mots aléatoires pour simuler du texte
def generate_random_content(length=256):
    words = ["".join(random.choices(string.ascii_lowercase, k=random.randint(3, 10))) for _ in range(length // 5)]
    return " ".join(words)[:length]


# -----------------------------------------------------------------------------
def get_message():
    message = {"id": generate_random_id(), "content": generate_random_content()}
    return json.dumps(message)


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    response = get_message()
    data = json.loads(response) if isinstance(response, str) else response

    msg_id = data["id"]
    msg_content = data["content"]

    print(msg_id)
    print(msg_content)
