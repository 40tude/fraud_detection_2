import threading
import time
from confluent_kafka import Producer, KafkaError
import sqlite3  # Pour le stockage temporaire


# -----------------------------------------------------------------------------
# Fonction pour envoyer un message sur Kafka
def send_message(message):
    try:
        producer.produce("my_topic", message)
        producer.flush()
    except KafkaError as e:
        if e.code() == KafkaError._ALL_BROKERS_DOWN:
            print("Connexion perdue. Enregistrement en local.")
            cursor.execute("INSERT INTO messages (message) VALUES (?)", (message,))
            conn.commit()
            monitor_thread.set()  # Déclenche le thread de surveillance


# -----------------------------------------------------------------------------
# Agent de Surveillance de la Connexion
def monitor_connection():
    while True:
        if monitor_thread.is_set():
            try:
                # Tente de produire un message vide comme test de connexion
                producer.produce("my_topic", b"")
                producer.flush()
                print("Connexion rétablie. Envoi des messages stockés...")
                resend_messages()
                monitor_thread.clear()  # Réinitialise le thread de surveillance
            except KafkaError:
                time.sleep(10)  # Réessaie après un certain délai


# -----------------------------------------------------------------------------
# Fonction pour vider le buffer local et renvoyer les messages
def resend_messages():
    cursor.execute("SELECT id, message FROM messages")
    messages = cursor.fetchall()
    for msg_id, message in messages:
        try:
            producer.produce("my_topic", message)
            producer.flush()
            cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
            conn.commit()
        except KafkaError:
            break  # Stoppe si la connexion est de nouveau interrompue


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # Configurer le Producteur Kafka
    conf = {"bootstrap.servers": "localhost:9092", "client.id": "my-producer"}
    producer = Producer(conf)

    # Initialiser la base SQLite pour stockage temporaire
    conn = sqlite3.connect("buffered_messages.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, message TEXT)")
    conn.commit()

    monitor_thread = threading.Event()
    monitoring_thread = threading.Thread(target=monitor_connection)
    monitoring_thread.start()

    # Exemple d'envoi de message
    send_message("Hello, Kafka!")
