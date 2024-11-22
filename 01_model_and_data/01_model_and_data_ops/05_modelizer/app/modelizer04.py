import os
import logging
import uvicorn
import pandas as pd
from fastapi.requests import Request
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models_loader import get_models
from schemas import InputData
from utils import make_prediction
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------- #
load_dotenv()
logger.info("Loading models...")
latest_mod, previous_mod = get_models()
current_mod = latest_mod
logger.info(f"Models loaded: latest version is {latest_mod.version}, previous version is {previous_mod.version}")

app = FastAPI()

# Configure the template folder
# templates = Jinja2Templates(directory="templates")
# logger.info("Template directory set to 'templates'")
templates = Jinja2Templates(directory=os.path.join(os.getcwd(), "templates"))
logger.info(f"Template directory set to '{os.path.join(os.getcwd(), 'templates')}'")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ----------------------------------------------------------------------------- #
@app.get("/get_model_ver")
async def get_model_ver():
    logger.info(f"Current model version requested: {current_mod.version}")
    return {"version": f"{current_mod.version}"}


# ----------------------------------------------------------------------------- #
@app.get("/switch_model_ver")
async def switch_model_ver():
    global current_mod
    current_mod = previous_mod if current_mod == latest_mod else latest_mod
    logger.info(f"Model version switched. Current version: {current_mod.version}")
    return {"version": f"{current_mod.version}"}


# ----------------------------------------------------------------------------- #
@app.post("/predict")
async def predict(data: InputData):
    try:
        logger.info("Prediction request received.")
        df = pd.DataFrame(data=data.data, columns=data.columns, index=data.index)
        logger.info(f"DataFrame created with shape: {df.shape}")
        prediction = make_prediction(current_mod.loaded_model, df)
        logger.info("Prediction successfully made.")
        return {"prediction": f"{prediction}"}
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Check that the number of parameters and their spelling are correct.",
        )


# ----------------------------------------------------------------------------- #
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logger.info("Root endpoint accessed.")
    return templates.TemplateResponse("home.html", {"request": request})


# ----------------------------------------------------------------------------- #
if __name__ == "__main__":
    port = 8005  # make sure this match the port number used in docker-compose
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
    # uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
