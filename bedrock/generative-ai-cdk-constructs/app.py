#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  BedrockKnowledgeBaseStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

kb_for_bedrock_stack = BedrockKnowledgeBaseStack(app, "BedrockKnowledgeBaseStack",
  env=AWS_ENV)

app.synth()
