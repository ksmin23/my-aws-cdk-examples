#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  # RandomStringsLambdaFnStack,
  LoggingApiCallsToFirehoseStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

# lambda_apigw_stack = RandomStringsLambdaFnStack(app, "RandomStringsLambdaFnStack",
#   env=APP_ENV
# )

apigw_stack = LoggingApiCallsToFirehoseStack(app, "LoggingApiCallsToFirehoseStack",
  # lambda_apigw_stack.lambda_fn,
  env=APP_ENV
)
# apigw_stack.add_dependency(lambda_apigw_stack)

app.synth()
