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


class FirehoseDataProcLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    firehose_data_transform_lambda_config = self.node.try_get_context('firehose_data_tranform_lambda')
    LAMBDA_LAYER_CODE_S3_BUCKET = firehose_data_transform_lambda_config['s3_bucket_name']
    LAMBDA_LAYER_CODE_S3_OBJ_KEY = firehose_data_transform_lambda_config['s3_object_key']

    s3_lambda_layer_lib_bucket = s3.Bucket.from_bucket_name(self, "LambdaLayerS3Bucket", LAMBDA_LAYER_CODE_S3_BUCKET)
    lambda_lib_layer = aws_lambda.LayerVersion(self, "SchemaValidatorLib",
      layer_version_name="fastavro-lib",
      compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_11],
      code=aws_lambda.Code.from_bucket(s3_lambda_layer_lib_bucket, LAMBDA_LAYER_CODE_S3_OBJ_KEY)
    )

    data_firehose_configuration = self.node.try_get_context("data_firehose_configuration")
    dest_iceberg_table_config = data_firehose_configuration["destination_iceberg_table_configuration"]
    dest_iceberg_table_unique_keys = dest_iceberg_table_config.get("unique_keys", None)
    dest_iceberg_table_unique_keys = ",".join(dest_iceberg_table_unique_keys) if dest_iceberg_table_unique_keys else ""

    LAMBDA_FN_NAME = "FirehoseToIcebergTransformer"
    self.data_proc_lambda_fn = aws_lambda.Function(self, "FirehoseToIcebergTransformer",
      runtime=aws_lambda.Runtime.PYTHON_3_11,
      function_name=LAMBDA_FN_NAME,
      handler="firehose_to_iceberg_transformer.lambda_handler",
      description="Transform records to Apache Iceberg table",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python/IcebergTransformer')),
      environment={
        "IcebergeDatabaseName": dest_iceberg_table_config["database_name"],
        "IcebergTableName": dest_iceberg_table_config["table_name"],
        "IcebergTableUniqueKeys": dest_iceberg_table_unique_keys
      },
      timeout=cdk.Duration.minutes(5),
      #XXX: set memory size appropriately
      memory_size=256,
      layers=[lambda_lib_layer]
    )

    log_group = aws_logs.LogGroup(self, "FirehoseToIcebergTransformerLogGroup",
      #XXX: Circular dependency between resources occurs
      # if aws_lambda.Function.function_name is used
      # instead of literal name of lambda function such as "FirehoseToIcebergTransformer"
      log_group_name=f"/aws/lambda/{LAMBDA_FN_NAME}",
      retention=aws_logs.RetentionDays.THREE_DAYS,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )
    log_group.grant_write(self.data_proc_lambda_fn)


    cdk.CfnOutput(self, 'FirehoseDataProcFuncName',
      value=self.data_proc_lambda_fn.function_name,
      export_name=f'{self.stack_name}-FirehoseDataProcFuncName')