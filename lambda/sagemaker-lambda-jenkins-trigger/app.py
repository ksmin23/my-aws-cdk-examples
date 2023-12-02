#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  SageMakerLambdaJenkinsTriggerStack
)

import aws_cdk as cdk


APP_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

sm_lambda_jenkins_trigger_stack = SageMakerLambdaJenkinsTriggerStack(app, "ScheduledLambdaStack",
  env=APP_ENV
)

app.synth()
