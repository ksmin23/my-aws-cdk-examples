from urllib.parse import urlparse

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_lambda,
  aws_s3 as s3
)
from constructs import Construct

class SageMakerLambdaLayerStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    LAMBDA_LAYER_LIB_S3_PATH = self.node.try_get_context('lambda_layer_lib_s3_path')
    parse_result = urlparse(LAMBDA_LAYER_LIB_S3_PATH)
    S3_BUCKET_NAME = parse_result.netloc
    lambda_layer_s3_bucket = s3.Bucket.from_bucket_name(self, "LambdaLayerS3Bucket", S3_BUCKET_NAME)
    lambda_layer_s3_object_key = parse_result.path.lstrip('/')

    sagemaker_sdk_lib = aws_lambda.LayerVersion(self, "SageMakerPySDKLib",
      layer_version_name="sagemaker-python-sdk-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_10],
      code=aws_lambda.Code.from_bucket(lambda_layer_s3_bucket, lambda_layer_s3_object_key),
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    self.lambda_layer = sagemaker_sdk_lib

