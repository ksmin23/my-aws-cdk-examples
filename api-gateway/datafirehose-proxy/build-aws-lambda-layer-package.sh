#!/bin/bash -

VERSION=1.10.0
PY_VERSION=3.11
LAMBDA_LAYER_NAME=fastavro-lib-${VERSION}-py-${PY_VERSION}
S3_PATH=$1

docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.11" /bin/sh -c "pip install fastavro==${VERSION} -t python/lib/python3.11/site-packages/; exit"

zip -q -r ${LAMBDA_LAYER_NAME}.zip python >/dev/null
aws s3 cp --quiet ${LAMBDA_LAYER_NAME}.zip s3://${S3_PATH}/${LAMBDA_LAYER_NAME}.zip
echo "[Lambda_Layer_Code_S3_Path] s3://${S3_PATH}/${LAMBDA_LAYER_NAME}.zip"

