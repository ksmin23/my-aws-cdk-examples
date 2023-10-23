#!/bin/bash -

export PATH=/home/ubuntu/.local/bin:$PATH

source /home/ubuntu/env_vars.sh

mlflow server \
  --default-artifact-root ${BUCKET} \
  --backend-store-uri mysql+pymysql://${USERNAME}:${PASSWORD}@${DB_EDNPOINT}/${DATABASE} \
  --port 5000 \
  --host 0.0.0.0
