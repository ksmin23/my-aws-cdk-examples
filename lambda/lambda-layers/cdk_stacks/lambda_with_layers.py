#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_lambda,
  aws_s3 as s3
)
from constructs import Construct


class LambdaLayersStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    S3_BUCKET_LAMBDA_LAYER_LIB = self.node.try_get_context('s3_bucket_lambda_layer_lib')
    s3_lib_bucket = s3.Bucket.from_bucket_name(self, "LambdaLayerS3Bucket", S3_BUCKET_LAMBDA_LAYER_LIB)

    pytz_lib_layer = aws_lambda.LayerVersion(self, "PyTZLib",
      layer_version_name="pytz-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_7],
      code=aws_lambda.Code.from_bucket(s3_lib_bucket, "var/pytz-lib.zip")
    )

    es_lib_layer = aws_lambda.LayerVersion(self, "ESLib",
      layer_version_name="es-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_7],
      code=aws_lambda.Code.from_bucket(s3_lib_bucket, "var/es-lib.zip")
    )

    lambda_fn = aws_lambda.Function(self, "LambdaLayerTest",
      runtime=aws_lambda.Runtime.PYTHON_3_7,
      function_name="LambdaLayerTest",
      handler="lambda_layer_test.lambda_handler",
      description="Lambda Layer Test",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      timeout=cdk.Duration.minutes(5),
      layers=[es_lib_layer, pytz_lib_layer],
      vpc=vpc
    )
