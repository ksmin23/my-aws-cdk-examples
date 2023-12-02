#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  CognitoUserPoolStack,
  KinesisDataStreamsStack,
  KdsProxyWithCognitoStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

user_pool_stack = CognitoUserPoolStack(app, "CognitoUserPoolStack",
  env=APP_ENV
)

kds_stack = KinesisDataStreamsStack(app, 'KinesisDataStreamsStack',
  env=APP_ENV)

kds_proxy_apigw = KdsProxyWithCognitoStack(app, 'ApiGwKdsProxyWithCognitoStack',
  user_pool_stack.user_pool,
  env=APP_ENV
)
kds_proxy_apigw.add_dependency(kds_stack)

app.synth()
