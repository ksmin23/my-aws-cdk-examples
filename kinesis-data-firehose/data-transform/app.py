#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  FirehoseDataTransformLambdaStack,
  KinesisFirehoseStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

firehose_data_transform_lambda = FirehoseDataTransformLambdaStack(app,
  'FirehoseDataTransformLambdaStack',
  env=AWS_ENV
)

firehose_stack = KinesisFirehoseStack(app, 'FirehoseDataTransformStack',
  firehose_data_transform_lambda.schema_validator_lambda_fn,
  env=AWS_ENV
)
firehose_stack.add_dependency(firehose_data_transform_lambda)

app.synth()