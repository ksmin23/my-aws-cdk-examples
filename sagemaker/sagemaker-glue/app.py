#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  SageMakerStudioStack,
)

APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'SageMakerGlueVPCStack',
  env=APP_ENV)

sm_studio_stack = SageMakerStudioStack(app, 'SageMakerStudioDomainStack',
  vpc_stack.vpc,
  env=APP_ENV
)
sm_studio_stack.add_dependency(vpc_stack)

app.synth()
