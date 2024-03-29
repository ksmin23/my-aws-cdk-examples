#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  DynamoDBStack,
  DynamoDBCrudHttpApiStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()
vpc_stack = VpcStack(app, 'DynamoDBCrudHttpApiVpcStack',
  env=AWS_ENV)

dynamodb_stack = DynamoDBStack(app, 'DynamoDBTableForHttpApiStack')
dynamodb_stack.add_dependency(vpc_stack)

dynamodb_crud_http_apigw = DynamoDBCrudHttpApiStack(app, 'DynamoDBCrudHttpApiGWStack',
  dynamodb_stack.dynamodb_table,
  env=AWS_ENV
)
dynamodb_crud_http_apigw.add_dependency(dynamodb_stack)

app.synth()
