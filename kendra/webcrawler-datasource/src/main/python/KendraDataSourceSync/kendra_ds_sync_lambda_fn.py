# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# https://github.com/aws-samples/amazon-kendra-langchain-extensions/blob/main/kendra_retriever_samples/kendra-docs-index.yaml

import json
import logging
import os
import traceback

import boto3
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

INDEX_ID = os.environ['INDEX_ID']
DS_ID = os.environ['DS_ID']
AWS_REGION = os.environ['AWS_REGION']
KendraClient = boto3.client('kendra', region_name=AWS_REGION)


def start_data_source_sync(dsId, indexId):
  logger.info(f"start_data_source_sync(dsId={dsId}, indexId={indexId})")
  try:
    resp = KendraClient.start_data_source_sync_job(Id=dsId, IndexId=indexId)
    logger.info(f"response:" + json.dumps(resp))
  except Exception as ex:
    traceback.print_exc()
    raise ex


def lambda_handler(event, context):
  logger.info("Received event: %s" % json.dumps(event))

  status = cfnresponse.SUCCESS
  request_type = event.get('RequestType', None)

  if request_type == 'Create':
    try:
      start_data_source_sync(DS_ID, INDEX_ID)
    except Exception as ex:
      status = cfnresponse.FAILED

  if request_type == 'Create': pass
  if request_type == 'Update': pass
  if request_type == 'Delete': pass

  cfnresponse.send(event, context, status, {}, None)
  return status
