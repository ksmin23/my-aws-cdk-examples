#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
 FirehoseToS3Stack,
 FirehoseDataProcLambdaStack
)


AWS_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

lambda_fn_stack = FirehoseDataProcLambdaStack(app, "FirehoseDataProcLambdaStack",
  env=AWS_ENV
)

firehose_stack = FirehoseToS3Stack(app, "FirehoseToS3Stack",
  lambda_fn_stack.metadata_extract_lambda_fn,
  env=AWS_ENV
)
firehose_stack.add_dependency(lambda_fn_stack)

app.synth()
