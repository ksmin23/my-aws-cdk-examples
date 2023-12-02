#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  VpcStack,
  DynamoDBStack,
  ApiGatewayDynamoDBStack
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

dynamodb_stack = DynamoDBStack(app, "DynamoDBStack",
  env=APP_ENV
)
dynamodb_stack.add_dependency(vpc_stack)

apigw_stack = ApiGatewayDynamoDBStack(app, "ApiGatewayDynamoDBStack",
  dynamodb_stack.dynamodb_table,
  env=APP_ENV
)
apigw_stack.add_dependency(dynamodb_stack)

app.synth()
