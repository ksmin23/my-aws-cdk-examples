#!/bin/bash -

LAMBDA_LAYER_NAME=fastavro-lib
S3_PATH=$1
REQUIREMENTS=${2:-requirements-dev.txt}

mkdir -p python_modules

step=0
while IFS= read -r line
do
  if [ "${line}" = "#[[layers]]" ]; then
    step=1
  elif [ ${step} = 1 ]; then
    step=2
  fi

  if [ ${step} = 2 ]; then
    if [ -z "${line}" ]; then
      step=0
    else
      pip install -q ${line} -t python_modules
    fi
  fi
done <${REQUIREMENTS}

mv python_modules python
zip -q -r ${LAMBDA_LAYER_NAME}.zip python/
aws s3 cp --quiet ${LAMBDA_LAYER_NAME}.zip s3://${S3_PATH}/${LAMBDA_LAYER_NAME}.zip
echo "[Lambda_Layer_Code_S3_Path] s3://${S3_PATH}/${LAMBDA_LAYER_NAME}.zip"
