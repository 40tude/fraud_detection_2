import pandas as pd


# In DEMO_MODE we force 25% of the records to have a non-NULL 'fraud_confirmed' feature
# Otherwise all records having a non-NULL 'fraud_confirmed' feature are used to create the CSV file
k_DEMO_MODE = True

# In DEBUG_MODE we force 1 record have a non-NULL 'fraud_confirmed' feature
k_DEBUG_MODE = True


k_AssetsDir = "../../04_data"
k_FileName = "fraud_test.csv"


# -----------------------------------------------------------------------------
filename_in = Path(k_AssetsDir) / k_FileName
df = pd.read_csv(filename_in)

# Alternative (AWS S3 bucket)
# df = pd.read_csv("https://lead-program-assets.s3.eu-west-3.amazonaws.com/M05-Projects/fraudTest.csv")

df.columns = df.columns.str.lower()
df.head(3)
