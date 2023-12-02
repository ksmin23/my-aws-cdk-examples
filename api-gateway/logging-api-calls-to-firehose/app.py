#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  LoggingApiCallsToFirehoseStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

apigw_stack = LoggingApiCallsToFirehoseStack(app, "LoggingApiCallsToFirehoseStack",
  env=APP_ENV
)

app.synth()
