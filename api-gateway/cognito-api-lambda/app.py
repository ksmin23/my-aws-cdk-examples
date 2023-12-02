#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  CognitoUserPoolStack,
  HelloWorldLambdaFnStack,
  CognitoProtectedApiStack
)

import aws_cdk as cdk


APP_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

user_pool_stack = CognitoUserPoolStack(app, "CognitoUserPoolStack",
  env=APP_ENV
)

lambda_apigw_stack = HelloWorldLambdaFnStack(app, "HelloWorldLambdaFnStack",
  env=APP_ENV
)
lambda_apigw_stack.add_dependency(user_pool_stack)

apigw_stack = CognitoProtectedApiStack(app, "CognitoProtectedApiStack",
  user_pool_stack.user_pool,
  lambda_apigw_stack.lambda_fn,
  env=APP_ENV
)
apigw_stack.add_dependency(lambda_apigw_stack)

app.synth()
