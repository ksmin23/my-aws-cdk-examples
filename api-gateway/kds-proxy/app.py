#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  KinesisDataStreamsStack,
  KdsProxyStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

kds_stack = KinesisDataStreamsStack(app, 'KinesisDataStreamsStack',
  env=AWS_ENV)

kds_proxy_apigw = KdsProxyStack(app, 'ApiGwKdsProxyStack',
  env=AWS_ENV
)
kds_proxy_apigw.add_dependency(kds_stack)

app.synth()
