conda create --name extractor_sql_no_docker python=3.12 -y
conda activate extractor_sql_no_docker
code .

modifier secrets.ps1

conda install psycopg2-binary -c conda-forge -y
conda install sqlalchemy -c conda-forge -y
conda install pandas -c conda-forge -y
conda install fsspec -c conda-forge -y
conda install s3fs -c conda-forge -y
