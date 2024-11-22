./secrets.ps1
docker run  -e DATA_URL=$env:AWS_REGION -e AWS_ACCESS_KEY_ID=$env:AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$env:AWS_SECRET_ACCESS_KEY client_predict
