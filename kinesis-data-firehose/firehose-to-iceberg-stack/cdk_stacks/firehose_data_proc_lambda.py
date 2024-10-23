#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_lambda,
  aws_logs
)
from constructs import Construct


class FirehoseDataProcLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    dest_iceberg_table_config = self.node.try_get_context("destination_iceberg_table_configuration")

    LAMBDA_FN_NAME = "FirehoseToIcebergTransformer"
    self.data_proc_lambda_fn = aws_lambda.Function(self, "FirehoseToIcebergTransformer",
      runtime=aws_lambda.Runtime.PYTHON_3_11,
      function_name=LAMBDA_FN_NAME,
      handler="firehose_to_iceberg_transformer.lambda_handler",
      description="Transform records to Apache Iceberg table",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      environment={
        "IcebergeDatabaseName": dest_iceberg_table_config["database_name"],
        "IcebergTableName": dest_iceberg_table_config["table_name"]
      },
      timeout=cdk.Duration.minutes(5),
      #XXX: set memory size appropriately
      memory_size=256
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
