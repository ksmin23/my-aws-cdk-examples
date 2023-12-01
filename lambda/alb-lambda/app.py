#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  VpcStack,
  AlbLambdaStack
)

import aws_cdk as cdk


APP_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

vpc_stack = VpcStack(app, "AlbLambdaVpcStack",
  env=APP_ENV
)

alb_lambda_stack = AlbLambdaStack(app, "AlbLambdaStack",
  vpc_stack.vpc,
  env=APP_ENV
)
alb_lambda_stack.add_dependency(vpc_stack)

app.synth()
