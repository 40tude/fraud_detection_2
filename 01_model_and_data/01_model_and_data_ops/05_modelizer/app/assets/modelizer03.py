import os
import uvicorn
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from models_loader import get_models
from schemas import InputData
from utils import make_prediction
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
load_dotenv()
latest_mod, previous_mod = get_models()
current_mod = latest_mod
app = FastAPI()


# -----------------------------------------------------------------------------
@app.get("/get_model_ver")
async def get_model_ver():
    return {"version": f"{current_mod.version}"}


# -----------------------------------------------------------------------------
@app.get("/switch_model_ver")
async def switch_model_ver():
    global current_mod
    current_mod = previous_mod if current_mod == latest_mod else latest_mod
    return {"version": f"{current_mod.version}"}


# -----------------------------------------------------------------------------
@app.post("/predict")
async def predict(data: InputData):
    try:
        df = pd.DataFrame(data=data.data, columns=data.columns, index=data.index)
        prediction = make_prediction(current_mod.loaded_model, df)
        return {"prediction": f"{prediction}"}
    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=500,
            detail="Check that the number of parameters and their spelling are correct.",
        )


# -----------------------------------------------------------------------------
@app.get("/docs")
async def get_docs():
    return {"docs_url": "/docs"}


# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
        <html>
            <head>
                <title>Modelizer</title>
            </head>
            <body>
                <h1>Welcome to Fraud Detection 2 Modelizer</h1>
                <ul>
                    <li>Use the endpoint <code>/predict</code> to make predictions</li>
                    <li>Use the endpoint <code>/docs</code> to test the API<br />
                        <ul>    
                            <li>Once the "/predict" panel is oen, click the "Try it out" button</li> 
                            <li>For a first test, copy'n paste the line below (from "{" to "}", both included)</li>
                            <li>This is not a fraudulent transaction, the prediction will be 0
                            <div> 
                            <code>
{
    "columns": ["trans_date_trans_time", "cc_num", "merchant", "category", "amt", "first", "last", "gender", "street", "city", "state", "zip", "lat", "long", "city_pop", "job", "dob", "trans_num", "unix_time", "merch_lat", "merch_long", "is_fraud"],
    "index": [164481],
    "data": [["2024-10-31 15:58:29", 38530489946071, "fraud_Cole, Hills and Jewess", "home", 22.9, "Laura", "Johns", "F", "95835 Garcia Rue", "Arcadia", "SC", 29320, 34.9572, -81.9916, 530, "Animal technologist", "1989-05-14", "fd6f5d5606f49ffbc33c2a28dfe006f1", 1730390309560, 34.831131, -82.885952, 0]]
}
                            </code></div></li>

                            

                            <li>For a second test, copy'n paste the line below.</li>
                            <li>This is a fraudulent transaction, the prediction will be 1
                            <div> 
                            <code>


{
    "columns": ["trans_date_trans_time", "cc_num", "merchant", "category", "amt", "first", "last", "gender", "street", "city", "state", "zip", "lat", "long", "city_pop", "job", "dob", "trans_num", "unix_time", "merch_lat", "merch_long", "is_fraud"],
    "index": [1781],
    "data": [["2020-06-21 22:37", 6564459919350820, "fraud_Nienow PLC", "entertainment", 620.33, "Douglas", "Willis", "M", "619 Jeremy Garden Apt. 681", "Benton", "WI", 53803, 42.5545, -90.3508, 1306, "Public relations officer", "1958-09-10", "47a9987ae81d99f7832a54b29a77bf4b", 1371854247, 42.771834, -90.158365, 1]]
}
                            </code></div></li>


                        </ul>
                    </li>
                </ul>
                <p>&nbsp;</p>

            </body>
        </html>
    """
    return html_content


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
