# Baseline model

* This code is the baseline model used by the `fraud_detection_2` project
* It is based on the sklearn template available here : ``02_train_code\02_sklearn\01_template`` 
* Feel free to read `02_train_code\02_sklearn\01_template\README.md` to understand how the code works

# Note
* In order to run train.py locally in WIN11 to debug ...
* It might be smart to create virtual env and run the train.py from VSCode
* If you want to do so then follow the steps below : 

```powershell
conda create --name train_sklearn_no_docker python=3.12 -y
conda activate train_sklearn_no_docker
code .
```

```powershell
conda install mlflow seaborn imbalanced-learn fsspec s3fs -c conda-forge -y
```
* Then
    1. Make sure to add `mlruns/` to ``.gitignore``
    1. Run ``.\secrets.ps1`` from the VSCode Debug terminal



