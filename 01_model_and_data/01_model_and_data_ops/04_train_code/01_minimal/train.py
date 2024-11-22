import mlflow
import random
import datetime
from PIL import Image
from pathlib import Path


class ModelTrainer:
    def __init__(self) -> None:
        mlflow.log_param("Dummy_Param", 42)
        mlflow.set_tag("Author", "Philippe")

        image = Image.new("RGB", (100, 100), color=random.choice(["blue", "red", "blue", "orange", "green"]))
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"./img/{timestamp}_dummy_artifact.png"
        image.save(title)
        mlflow.log_artifact(title)
        return


if __name__ == "__main__":
    Path("./img").mkdir(parents=True, exist_ok=True)
    trainer = ModelTrainer()
