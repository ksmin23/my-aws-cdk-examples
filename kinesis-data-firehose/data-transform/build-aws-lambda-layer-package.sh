#!/bin/bash -

LAMBDA_LAYER_NAME=fastavro-lib
S3_PATH=$1

docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.9" /bin/sh -c "pip install fastavro==1.6.1 -t python/lib/python3.9/site-packages/; exit"

zip -q -r ${LAMBDA_LAYER_NAME}.zip python >/dev/null
aws s3 cp --quiet ${LAMBDA_LAYER_NAME}.zip s3://${S3_PATH}/${LAMBDA_LAYER_NAME}.zip
echo "[Lambda_Layer_Code_S3_Path] s3://${S3_PATH}/${LAMBDA_LAYER_NAME}.zip"
