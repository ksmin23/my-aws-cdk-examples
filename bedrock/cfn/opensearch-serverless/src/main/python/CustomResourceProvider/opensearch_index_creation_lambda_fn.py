#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import logging
import os
import time
import traceback
from datetime import datetime
from urllib.parse import urlparse

from botocore.exceptions import ClientError
import cfnresponse

import boto3
from opensearchpy import (
  OpenSearch,
  RequestsHttpConnection,
  AWSV4SignerAuth,
  NotFoundError
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


INDEX_SETTING_BY_MODEL_ID = {
  "amazon.titan-embed-text-v1": {
    "settings": {"index": {"knn": True, "knn.algo_param.ef_search": 512}},
    "mappings": {
      "properties": {
        "vector_field": {
          "type": "knn_vector",
          "dimension": 1536,
          "method": {
            "name": "hnsw",
            "engine": "faiss",
            "parameters": {"ef_construction": 512, "m": 16},
            "space_type": "l2"
          }
        }
      }
    }
  },
  "amazon.titan-embed-text-v2:0": {
    "settings": {"index": {"knn": True, "knn.algo_param.ef_search": 512}},
    "mappings": {
      "properties": {
        "vector_field": {
          "type": "knn_vector",
          "dimension": 1536,
          "method": {
            "name": "hnsw",
            "engine": "faiss",
            "parameters": {"ef_construction": 512, "m": 16},
            "space_type": "l2"
          }
        }
      }
    }
  },
  "cohere.embed-english-v3": {
    "settings": {"index": {"knn": True, "knn.algo_param.ef_search": 512}},
    "mappings": {
      "properties": {
        "vector_field": {
          "type": "knn_vector",
          "dimension": 1024,
          "method": {
            "name": "hnsw",
            "engine": "faiss",
            "parameters": {"ef_construction": 512, "m": 16},
            "space_type": "l2"
          }
        }
      }
    }
  },
  "cohere.embed-multilingual-v3": {
    "settings": {"index": {"knn": True, "knn.algo_param.ef_search": 512}},
    "mappings": {
      "properties": {
        "vector_field": {
          "type": "knn_vector",
          "dimension": 1024,
          "method": {
            "name": "hnsw",
            "engine": "faiss",
            "parameters": {"ef_construction": 512, "m": 16},
            "space_type": "l2"
          }
        }
      }
    }
  }
}


def get_opensearch_serverless_client(opensearch_url, region_name='us-east-1'):
  credentials = boto3.Session(region_name=region_name).get_credentials()
  awsauth = AWSV4SignerAuth(credentials, region_name, 'aoss')
  host = urlparse(opensearch_url).netloc

  client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
  )

  return client


def create_index_with_retries(opensearch_client, index_name, request_body):
  for _ in range(10):
    try:
      response = opensearch_client.indices.create(index_name, body=request_body)
      logger.info(response)
      logger.info(f"Created index: {index_name}, waiting for index to get ready")
      time.sleep(120)
      return response
    except Exception as _:
      logger.info("Sleeping for 10 seconds and retrying.")
      time.sleep(10)
  else:
    raise RuntimeError('IndexCreationFailure')


def delete_index_if_exists(opensearch_client, index_name):
  try:
    if opensearch_client.indices.exists(index_name):
      response = opensearch_client.indices.delete(index=index_name)
      logger.info(response)
      logger.info(f"Deleted index {index_name}, sleeping for 1 min")
      time.sleep(60)
      return response
  except NotFoundError:
    logger.info("Index {index_name} not found, skipping deletion")
  except Exception as ex:
    logger.info(f"Deletion of index {index_name} failed, reason: {ex}")
    traceback.print_exc()
    raise RuntimeError('IndexDeletionFailure')


def update_data_access_policy_with_caller_arn(policy_name, region_name='us-east-1'):
  sts_client = boto3.client("sts", region_name=region_name)
  caller_arn = sts_client.get_caller_identity()['Arn']

  oss_client = boto3.client("opensearchserverless", region_name=region_name)
  response = oss_client.get_access_policy(name=policy_name, type="data")
  if response['ResponseMetadata']['HTTPStatusCode'] != 200:
    logger.info(response['ResponseMetadata'])
    return False

  access_policy_detail = response['accessPolicyDetail']
  updated_data_access_policy = list(access_policy_detail['policy'])
  if caller_arn not in updated_data_access_policy[0]['Principal']:
    updated_data_access_policy[0]['Principal'].append(caller_arn)

  response = oss_client.update_access_policy(
    name=policy_name,
    policyVersion=access_policy_detail['policyVersion'],
    policy=json.dumps(updated_data_access_policy),
    description=f"Policy updated at {datetime.now()}",
    type="data"
  )

  if response['ResponseMetadata']['HTTPStatusCode'] != 200:
    return False

  logger.info(response['ResponseMetadata'])
  logger.info("Updated data access policy, sleeping for 2 minutes for permissions to propagate")
  time.sleep(120)
  return True


def on_create(event, context):
  props = event["ResourceProperties"]
  logger.info("Create new OpenSearch index with props %s" % props)

  region_name = os.environ['AWS_REGION']
  policy_name = props["data_access_policy_name"]

  logger.info(f"Updating data access policy: {policy_name}")
  res = update_data_access_policy_with_caller_arn(policy_name, region_name=region_name)
  if not res:
    cfnresponse.send(event, context, cfnresponse.FAILED, {}, physicalResourceId=index_name)
    return {"PhysicalResourceId": None}

  collection_endpoint = props["opensearch_endpoint"]
  index_name = props["index_name"]
  embedding_model_id = props["embedding_model_id"]
  index_request = json.dumps(INDEX_SETTING_BY_MODEL_ID[embedding_model_id])

  cfn_res_status = cfnresponse.SUCCESS
  try:
    logger.info(f"Creating index: {index_name}")
    opensearch_client = get_opensearch_serverless_client(collection_endpoint, region_name=region_name)
    create_index_with_retries(opensearch_client, index_name, index_request)
  except Exception as _:
    cfn_res_status = cfnresponse.FAILED

  cfnresponse.send(event, context, cfn_res_status, {}, physicalResourceId=index_name)
  return {"PhysicalResourceId": index_name}


def on_update(event, context):
  props = event["ResourceProperties"]
  old_props = event["OldResourceProperties"]
  logger.info("Updating OpenSearch index with new props %s, old props: %s" % (props, old_props))

  index_name = event["PhysicalResourceId"]
  if old_props == props:
    logger.info("Props are same, nothing to do")
    return {"PhysicalResourceId": index_name}

  logger.info("New props are different from old props. Index requires re-creation")

  region_name = os.environ['AWS_REGION']
  policy_name = props["data_access_policy_name"]

  logger.info(f"Updating data access policy: {policy_name}")
  res = update_data_access_policy_with_caller_arn(policy_name, region_name=region_name)
  if not res:
    cfnresponse.send(event, context, cfnresponse.FAILED, {}, physicalResourceId=index_name)
    return {"PhysicalResourceId": index_name}

  collection_endpoint = props["opensearch_endpoint"]

  old_index_name = old_props["index_name"]
  logger.info(f"Deleting old index: {old_index_name}")

  cfn_res_status = cfnresponse.SUCCESS
  try:
    opensearch_client = get_opensearch_serverless_client(collection_endpoint, region_name=region_name)
    delete_index_if_exists(opensearch_client, old_index_name)
  except Exception as _:
    cfn_res_status = cfnresponse.FAILED
    cfnresponse.send(event, context, cfn_res_status, {}, physicalResourceId=old_index_name)
    return {"PhysicalResourceId": old_index_name}

  new_index_name = props["index_name"]
  embedding_model_id = props["embedding_model_id"]
  index_request = json.dumps(INDEX_SETTING_BY_MODEL_ID[embedding_model_id])

  cfn_res_status = cfnresponse.SUCCESS
  try:
    logger.info(f"Creating index: {new_index_name}")
    opensearch_client = get_opensearch_serverless_client(collection_endpoint, region_name=region_name)
    create_index_with_retries(opensearch_client, new_index_name, index_request)
  except Exception as _:
    cfn_res_status = cfnresponse.FAILED

  cfnresponse.send(event, context, cfn_res_status, {}, physicalResourceId=new_index_name)
  return {"PhysicalResourceId": new_index_name}


def on_delete(event, context):
  index_name = event["PhysicalResourceId"]
  props = event["ResourceProperties"]
  logger.info(f"Deleting OpenSearch index {index_name} with props {props}")

  region_name = os.environ['AWS_REGION']
  collection_endpoint = props["opensearch_endpoint"]

  cfn_res_status = cfnresponse.SUCCESS
  try:
    opensearch_client = get_opensearch_serverless_client(collection_endpoint, region_name=region_name)
    delete_index_if_exists(opensearch_client, index_name)
  except Exception as _:
    cfn_res_status = cfnresponse.FAILED

  cfnresponse.send(event, context, cfn_res_status, {}, physicalResourceId=index_name)
  return {"PhysicalResourceId": index_name}


def lambda_handler(event, context):
  logger.info(f"Received event: {json.dumps(event)}")

  request_type = event["RequestType"]
  if request_type == "Create":
    return on_create(event, context)
  if request_type == "Update":
    return on_update(event, context)
  if request_type == "Delete":
    return on_delete(event, context)
  raise Exception(f"Invalid request type: {request_type}")
