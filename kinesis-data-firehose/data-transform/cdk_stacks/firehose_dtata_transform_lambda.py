#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import aws_cdk as cdk

from aws_cdk import (
  Stack,

  aws_lambda,
  aws_logs,
  aws_s3 as s3
)
from constructs import Construct


class FirehoseDataTransformLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    firehose_data_transform_lambda_config = self.node.try_get_context('firehose_data_tranform_lambda')
    LAMBDA_LAYER_CODE_S3_BUCKET = firehose_data_transform_lambda_config['s3_bucket_name']
    LAMBDA_LAYER_CODE_S3_OBJ_KEY = firehose_data_transform_lambda_config['s3_object_key']

    s3_lambda_layer_lib_bucket = s3.Bucket.from_bucket_name(self, "LambdaLayerS3Bucket", LAMBDA_LAYER_CODE_S3_BUCKET)
    lambda_lib_layer = aws_lambda.LayerVersion(self, "SchemaValidatorLib",
      layer_version_name="fastavro-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
      code=aws_lambda.Code.from_bucket(s3_lambda_layer_lib_bucket, LAMBDA_LAYER_CODE_S3_OBJ_KEY)
    )

    SCHEMA_VALIDATOR_LAMBDA_FN_NAME = "SchemaValidator"
    schema_validator_lambda_fn = aws_lambda.Function(self, "SchemaValidator",
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="SchemaValidator",
      handler="schema_validator.lambda_handler",
      description="Check if records have valid schema",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      timeout=cdk.Duration.minutes(5),
      #XXX: set memory size appropriately
      memory_size=256,
      layers=[lambda_lib_layer]
    )

    log_group = aws_logs.LogGroup(self, "SchemaValidatorLogGroup",
      #XXX: Circular dependency between resources occurs
      # if aws_lambda.Function.function_name is used
      # instead of literal name of lambda function such as "SchemaValidator"
      log_group_name="/aws/lambda/{}".format(SCHEMA_VALIDATOR_LAMBDA_FN_NAME),
      retention=aws_logs.RetentionDays.THREE_DAYS,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )
    log_group.grant_write(schema_validator_lambda_fn)

    self.schema_validator_lambda_fn = schema_validator_lambda_fn


    cdk.CfnOutput(self, 'FirehoseDataTransformFuncName',
      value=self.schema_validator_lambda_fn.function_name,
      export_name=f'{self.stack_name}-FirehoseDataTransformFuncName')
