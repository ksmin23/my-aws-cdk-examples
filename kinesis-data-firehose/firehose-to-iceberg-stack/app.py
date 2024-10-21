#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  FirehoseToIcebergStack,
  FirehoseDataProcLambdaStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

firehose_data_transform_lambda = FirehoseDataProcLambdaStack(app,
  'FirehoseDataTransformLambdaStack',
  env=AWS_ENV
)

firehose_stack = FirehoseToIcebergStack(app, 'FirehoseToIcebergStack',
  firehose_data_transform_lambda.data_proc_lambda_fn,
  env=AWS_ENV
)
firehose_stack.add_dependency(firehose_data_transform_lambda)

app.synth()
