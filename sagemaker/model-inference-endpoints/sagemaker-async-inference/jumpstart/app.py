#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  ASRAsyncEndpointStack,
  SageMakerAsyncEndpointAutoScalingStack
)

APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

sm_asr_endpoint = ASRAsyncEndpointStack(app, 'ASRAsyncEndpointStack',
  env=APP_ENV
)

sm_asr_endpoint_autoscale = SageMakerAsyncEndpointAutoScalingStack(app, 'ASRAsyncEndpointAutoScalingStack',
  sm_asr_endpoint.sagemaker_endpoint,
  env=APP_ENV
)
sm_asr_endpoint_autoscale.add_dependency(sm_asr_endpoint)

app.synth()
