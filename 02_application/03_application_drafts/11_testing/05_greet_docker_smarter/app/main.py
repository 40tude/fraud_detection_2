# Use the class User
from user import User
from PIL import Image
from pathlib import Path
import random
import datetime
import os

if __name__ == "__main__":
    bob = User(80386, "Zoubida", 42)
    print(bob.greet())

    my_password = os.getenv("PASSWORD", "CPE1704TKS")
    print(f"The password is : {my_password}")
    
    os.chdir(Path(__file__).resolve().parent)
    Path("../img").mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (100, 100), color=random.choice(["blue", "red", "blue", "orange", "green"]))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image.save(f"../img/{timestamp}_dummy_artifact.png")

