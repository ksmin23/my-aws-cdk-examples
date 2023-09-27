import json
import logging
import os
import traceback

from botocore.exceptions import ClientError
import cfnresponse
from sagemaker.jumpstart.model import JumpStartModel
from sagemaker.predictor import Predictor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL_ID = os.environ['MODEL_ID']
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
SAGEMAKER_IAM_ROLE_ARN = os.environ['SAGEMAKER_IAM_ROLE_ARN']
AWS_REGION = os.environ['AWS_REGION']


def deploy_sagemaker_jumpstart_model(model_id, endpoint_name, iam_role_arn):
  logger.info(f"Deploying SageMaker JumpStart Model(model_id={model_id}, endpoint_name={endpoint_name}, ...)")
  try:
    model = JumpStartModel(model_id=model_id,
      role=iam_role_arn)
    predictor = model.deploy(endpoint_name=endpoint_name,
      wait=False)
    logger.info(f"SageMaker Endpoint Name: {predictor.endpoint_name}")
    return predictor
  except Exception as ex:
    traceback.print_exc()
    raise ex


def lambda_handler(event, context):
  logger.info("Received event: %s" % json.dumps(event))

  status = cfnresponse.SUCCESS
  request_type = event.get('RequestType', None)

  if request_type == 'Create':
    try:
      predictor = deploy_sagemaker_jumpstart_model(MODEL_ID, ENDPOINT_NAME, SAGEMAKER_IAM_ROLE_ARN)
    except Exception as ex:
      status = cfnresponse.FAILED

  if request_type == 'Update': pass
  if request_type == 'Delete':
    try:
      logger.info(f"Deleting SageMaker Endpoint: {ENDPOINT_NAME}")

      predictor = Predictor(ENDPOINT_NAME)
      predictor.delete_model()
      predictor.delete_endpoint(delete_endpoint_config=True)
    except ClientError as ex:
      status = cfnresponse.SUCCESS
      traceback.print_exc()
    except Exception as ex:
      status = cfnresponse.FAILED
      traceback.print_exc()

  cfnresponse.send(event, context, status, {}, None)
  return status
