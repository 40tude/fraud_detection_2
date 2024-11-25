# fd2_drift_report_generator.y


# -----------------------------------------------------------------------------
# prelude
import os
import random
import inspect
import logging
import smtplib
import requests
import numpy as np
import pandas as pd

from pathlib import Path
from typing import Tuple
from datetime import datetime
from evidently.report import Report
from email.mime.text import MIMEText
from evidently.test_suite import TestSuite
from evidently.metric_preset import DataDriftPreset

# from evidently.test_preset import DataStabilityTestPreset
from evidently.pipeline.column_mapping import ColumnMapping

# Pour les mails
import smtplib
from email.mime.multipart import MIMEMultipart

# import evidently
# print(evidently.__version__)


# -----------------------------------------------------------------------------
# In demo mode it use the dataset to generates biased production dataset
k_DEMO_MODE = True

# In debug mode it limit the umber of samples to be used to generate the report and speed up the process
k_DEBUG_MODE = True

if k_DEBUG_MODE:
    k_Number_of_samples = 512  # ! Must be an even number >= 62
else:
    k_Number_of_samples = 10_000

k_Current_dir = Path(__file__).parent
k_Reports_Dir = k_Current_dir / "reports"
k_Analysis_Datasets_Dir = k_Current_dir / "analysis_datasets"

# Names of the datasets used for the analysis
k_Reference_Dataset_Dataset = "reference_sample.csv"
k_Production_Dataset_Dataset = "production_sample.csv"
k_Production_Drifted_Dataset = "production_drifted_sample.csv"

k_Data_Dir = k_Current_dir / "../../04_data"

# Set k_Fraud_Test_csv equal k_Fraud_Test_csv_Local OR k_Fraud_Test_csv_URL OR ...
k_Fraud_Test_csv_Local = Path(k_Data_Dir) / "fraud_test.csv"
k_Fraud_Test_csv_URL = "https://lead-program-assets.s3.eu-west-3.amazonaws.com/M05-Projects/fraudTest.csv"
k_Fraud_Test_csv = k_Fraud_Test_csv_Local

# Set k_Drift_Server_URL equal to k_Drift_Server_Local OR k_Drift_Server_Heroku OR ...
k_Drift_Server_Local = "http://127.0.0.1:5000"
k_Drift_Server_Heroku = "https://fd2-drift-server-485e8a3514d2.herokuapp.com/"
k_Drift_Server_URL = k_Drift_Server_Local

k_Drift_Server_upload_URL = f"{k_Drift_Server_URL}/upload"
k_Report_Link = f"{k_Drift_Server_URL}/reports?date="


# k_Production_csv_URL = "https://???????????????/validated.csv"


# -----------------------------------------------------------------------------
# Global logger
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
g_logger = logging.getLogger("fd2_drift_report_generator")


# -----------------------------------------------------------------------------
# Amounts (amt)                        : 80% of transactions are increased by 100%.
# Lat and long (merch_lat, merch_long) : 20% of transactions are shifted.
# Categories                           : 30% of transactions have their category changed in favor of a bias.
def bias_production_dataset(production_df: pd.DataFrame) -> pd.DataFrame:

    g_logger.info(f"{inspect.stack()[0][3]}()")

    # Créer une copie des données pour introduire un drift
    production_drifted_df = production_df.copy()

    # np.random.choice([1, 2.0], size=len(production_df), p=[0.7, 0.3]) :
    # Generates an array of size production_drifted_df['amt']
    #       Each element is worth 1 or 2
    #       Associated probabilities :
    #           70% of generated values will be 1.
    #           30% of generated values will be 2
    # So 30% of values will have been mult by 2 => Normally this should drift !!!
    production_drifted_df["amt"] = production_drifted_df["amt"] * np.random.choice(
        [1.0, 2.0], size=len(production_df), p=[0.2, 0.8]
    )

    # Drift 2: Modify latitudes and longitudes ('merch_lat', 'merch_long')
    # Introduce an artificial offset for certain transactions
    # ! INUTILE car les transactions sont sur tout le pays
    # production_drifted_df['merch_lat'] += np.random.choice([0, 0.1], size=len(production_df), p=[0.6, 0.4])
    # production_drifted_df['merch_long'] += np.random.choice([0, -0.1], size=len(production_df), p=[0.6, 0.4])

    # Drift 3: Modify category distribution
    # Introduce a bias in favor of certain categories
    # Get the categories
    categories = production_drifted_df["category"].unique()
    # Create a list of of the same length as the production_df DataFrame
    # [0.5]                                             : The first element of categories is chosen with a probability of 50%.
    # [0.5 / (len(categories) - 1)]                     : The remaining categories (all except the first) have equal probabilities.
    #                                                     Calculated as the remaining half (0.5) divided by the number of remaining categories (len(categories) - 1)
    # The multiplication for the remaining categories   : by (len(categories) - 1) generates a list of equal probabilities for the remaining categories.
    # If categories = ['A', 'B', 'C', 'D']
    # Then the first element ('A') has a probability of 50%. The other 3 categories ('B', 'C', 'D') each have a probability of : 0.5/3 = 16%
    # biased_categories will have 50% of A randomly distributed and the other categories are equiproblable and randomly distributed
    biased_categories = np.random.choice(
        categories, size=len(production_df), p=[0.5] + [0.5 / (len(categories) - 1)] * (len(categories) - 1)
    )

    # np.random.rand(len(production_df)): Generates an array of uniform random numbers between 0 and 1, of the same length as the production_df DataFrame.
    # Condition < 0.4: Checks whether each random number is less than 0.4.
    # Around 40% of rows will be selected
    # Effect: Creates a condition that is True for around 40% of rows, and False for the rest.
    # If true (< 0.4) the corresponding rows will receive the biased_categories values.
    # biased_categories: This can be an array, a list, or a single value containing the new biased categories to be applied.
    production_drifted_df["category"] = np.where(
        np.random.rand(len(production_df)) < 0.4,  # 40% of the row are modified
        biased_categories,  # New biased category
        production_drifted_df["category"],  # current category
    )

    production_drifted_df.to_csv(Path(k_Analysis_Datasets_Dir) / k_Production_Drifted_Dataset, index=False)

    return production_drifted_df


# -----------------------------------------------------------------------------
def fetch_datasets() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create two random samples if there are sufficient rows in the dataset.
    """

    # -------------------------------------------------------------------------
    # Is raise only from fetch_datasets()
    class InsufficientDataError(Exception):
        """Custom exception raised when there is not enough data in the dataset."""

        pass

    g_logger.info(f"{inspect.stack()[0][3]}()")

    # assert k_Number_of_samples % 2 == 0 and k_Number_of_samples >= 60
    if k_Number_of_samples % 2 != 0 or k_Number_of_samples < 60:
        raise ValueError(
            f"Invalid value for 'k_Number_of_samples': {k_Number_of_samples}. "
            "It must be an even number and at least 60."
        )

    # # Alternative (AWS S3 bucket)
    # # df = pd.read_csv(k_URL_Fraud_Test_csv)

    # fraud_test_file = Path(k_Local_Data_Dir) / k_Fraud_Test_csv_Local

    try:
        df = pd.read_csv(k_Fraud_Test_csv, nrows=k_Number_of_samples)
    except FileNotFoundError as e:
        g_logger.error(f"File '{k_Fraud_Test_csv}' not found. Ensure the file path is correct.")
        raise FileNotFoundError(f"File '{k_Fraud_Test_csv}' not found.") from e

    # Determine the number of rows
    num_rows: int = len(df)
    g_logger.info(f"Number of rows in the dataset: {num_rows}")

    # Stop if there are less than k_Number_of_samples rows
    # Indeed I want k_Number_of_samples/2 in one set and k_Number_of_samples/2 others rows in the other set
    if num_rows < k_Number_of_samples:
        g_logger.error("Not enough rows in the dataset. Exiting.")
        raise InsufficientDataError(
            f"Dataset contains only {num_rows} rows, but {k_Number_of_samples} rows are required."
        )

    # Take k_Number_of_samples/2 random rows for the reference sample
    reference_indices = random.sample(range(num_rows), int(k_Number_of_samples / 2))
    reference_df = df.iloc[reference_indices]

    # Take another k_Number_of_samples/2 random rows for the production sample (different from the first set)
    remaining_indices = list(set(range(num_rows)) - set(reference_indices))
    production_indices = random.sample(remaining_indices, int(k_Number_of_samples / 2))
    production_df = df.iloc[production_indices]

    # Save the samples to their respective files
    reference_sample_file = Path(k_Analysis_Datasets_Dir) / k_Reference_Dataset_Dataset
    production_sample_file = Path(k_Analysis_Datasets_Dir) / k_Production_Dataset_Dataset
    reference_df.to_csv(reference_sample_file, index=False)
    production_df.to_csv(production_sample_file, index=False)

    g_logger.info(f"Saved reference sample to: {reference_sample_file}")
    g_logger.info(f"Saved production sample to: {production_sample_file}")

    # reference_df = pd.read_csv(Path(k_AssetsDir) / k_Reference_Dataset_Dataset)
    reference_df.rename(columns={reference_df.columns[0]: "id"}, inplace=True)
    reference_df["trans_date_trans_time"] = pd.to_datetime(
        reference_df["trans_date_trans_time"], format="%Y-%m-%d %H:%M:%S"
    )
    reference_df["dob"] = pd.to_datetime(reference_df["dob"], format="%Y-%m-%d")
    reference_df["is_fraud"] = reference_df["is_fraud"].astype(bool)

    # production_df = pd.read_csv(Path(k_AssetsDir) / k_Production_Dataset_Dataset)
    production_df.rename(columns={production_df.columns[0]: "id"}, inplace=True)
    production_df["trans_date_trans_time"] = pd.to_datetime(
        production_df["trans_date_trans_time"], format="%Y-%m-%d %H:%M:%S"
    )
    production_df["dob"] = pd.to_datetime(production_df["dob"], format="%Y-%m-%d")
    production_df["is_fraud"] = production_df["is_fraud"].astype(bool)

    if k_DEMO_MODE:
        production_df = bias_production_dataset(production_df)

    return reference_df, production_df


# -----------------------------------------------------------------------------
def send_email(subject: str, body: str) -> None:

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    email_recipient = os.getenv("EMAIL_RECIPIENT")

    msg = MIMEMultipart("alternative")
    msg["From"] = smtp_user
    msg["To"] = email_recipient
    msg["Subject"] = subject

    body_html = f"""
        <html>
            <body>
                <p>{body}</p>
            </body>
        </html>
    """

    msg.attach(MIMEText(body_html, "html"))

    # Connect and send
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # protect the connexion
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, email_recipient, msg.as_string())
        g_logger.info("E-mail successfully sent.")
    except Exception as e:
        g_logger.info(f"Error sending e-mail. Did you run ./secrets.ps1 first ? : \n{e}")
    return


# -----------------------------------------------------------------------------
def generate_report(reference_df: pd.DataFrame, production_df: pd.DataFrame) -> None:

    g_logger.info(f"{inspect.stack()[0][3]}()")

    # Filtrer uniquement les colonnes numériques dans les DataFrames
    # Car le modèle n'utilise que les données numériques et qu'en plus en mode demo
    # on introduit du biais que sur certaines données numériques

    reference_numeric_df = reference_df.select_dtypes(include="number")
    production_numeric_df = production_df.select_dtypes(include="number")

    # Create a report for drift analysis
    data_drift_report = Report(metrics=[DataDriftPreset()])
    # column_mapping = ColumnMapping(
    #     numerical_features=numeric_columns,
    #     # categorical_features=["gender", "category"],
    #     datetime_features=["trans_date_trans_time", "dob"],
    #     target="is_fraud",
    #     id="id",
    # )
    # column_mapping=None => let it infer the mapping (works pretty well)
    data_drift_report.run(reference_data=reference_numeric_df, current_data=production_numeric_df, column_mapping=None)

    # Is there a global drift
    # Si plus de 50 % des features analysées présentent un drift statistiquement significatif
    # Une p-value faible (typiquement < 0.05) indique un drift statistiquement significatif pour cette feature
    results = data_drift_report.as_dict()
    global_drift_detected = results["metrics"][0]["result"]["dataset_drift"]
    g_logger.info(f"Global drift = {global_drift_detected}")

    # Display features with drift
    drift_by_columns = results["metrics"][1]["result"]["drift_by_columns"]
    drifted_features = [
        col
        for col, details in drift_by_columns.items()
        # Si la clé 'drift_detected' existe dans le dictionnaire, sa valeur sera retournée sinon on retourne False
        if details.get("drift_detected", False)
    ]
    g_logger.info(f"Features with drift: {drifted_features}")

    timestamp1 = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = k_Reports_Dir / f"data_drift_report_{timestamp1}.html"

    # we must derive timestamp2 from timestamp1, think at 11H59:59
    # Format of the route on the server => http://localhost:5000/reports?date=2024-11-24
    timestamp2 = datetime.strptime(timestamp1, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d")
    # report_link = f"http://localhost:5000/reports?date={timestamp2}"
    report_link = f"{k_Report_Link}{timestamp2}"

    if global_drift_detected:
        data_drift_report.save_html(str(output_file))
        g_logger.info(f"Saved biased production sample to: {output_file}")
        send_report(output_file)
        send_email(
            "ALERT: A global data drift detected!",
            f"A drift was detected. Check the report at: <a href='{report_link}'>here</a>.<br> In the list, look for <b>data_drift_report_{timestamp1}.html</b>",
        )
    elif drifted_features:
        # Pas de drift global mais au moins une feature dérive
        # report.save_html("data_drift_report.html")  # Stocker le rapport
        data_drift_report.save_html(str(output_file))
        g_logger.info(f"Saved biased production sample to: {output_file}")
        send_report(output_file)
        send_email(
            "WARNING: Feature-level drift detected",
            f"The following features show drift: {', '.join(drifted_features)}. Check the report at: <a href='{report_link}'>here</a><br> In the list, look for <b>data_drift_report_{timestamp1}.html</b>",
        )
    else:
        g_logger.info("No drift detected. No report saved.")

    return


# -----------------------------------------------------------------------------
def send_report(file_path: Path) -> None:

    g_logger.info(f"{inspect.stack()[0][3]}()")

    with open(file_path, "rb") as file:
        response = requests.post(k_Drift_Server_upload_URL, files={"file": file})

    if response.status_code == 200:
        g_logger.info("Drift report successfully uploaded")
    else:
        g_logger.error(f"Failed to upload the drift report. Response: {response.text}")

    return


# -----------------------------------------------------------------------------
if __name__ == "__main__":

    g_logger.info(f"{inspect.stack()[0][3]}()")

    g_logger.info(f"Current dir = {k_Current_dir}")

    k_Reports_Dir.mkdir(parents=True, exist_ok=True)
    g_logger.info(f"{k_Reports_Dir} created (if not already existing)")

    k_Analysis_Datasets_Dir.mkdir(parents=True, exist_ok=True)
    g_logger.info(f"{k_Analysis_Datasets_Dir} created (if not already existing)")

    reference_df, production_df = fetch_datasets()
    generate_report(reference_df, production_df)
