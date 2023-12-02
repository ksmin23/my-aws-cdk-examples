#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  VpcStack,
  CognitoUserPoolStack,
  DynamoDBStack,
  CognitoProtectedDynamoDBApiStack
)

import aws_cdk as cdk


APP_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

vpc_stack = VpcStack(app, "VpcStack",
  env=APP_ENV
)

user_pool_stack = CognitoUserPoolStack(app, "CognitoUserPoolStack",
  env=APP_ENV
)
user_pool_stack.add_dependency(vpc_stack)

dynamodb_stack = DynamoDBStack(app, "DynamoDBStack",
  env=APP_ENV
)
dynamodb_stack.add_dependency(user_pool_stack)

apigw_stack = CognitoProtectedDynamoDBApiStack(app, "CognitoProtectedDynamoDBApiStack",
  user_pool_stack.user_pool,
  dynamodb_stack.dynamodb_table,
  env=APP_ENV
)
apigw_stack.add_dependency(dynamodb_stack)

app.synth()
