#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  KdsStack,
  GlueStreamingJobStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

kds_stack = KdsStack(app, 'KinesisStreamForGlueStreamingJob')

app.synth()
