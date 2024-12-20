#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  MemoryDBStack
)


APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'MemoryDBVPCStack',
  env=APP_ENV)

memorydb_stack = MemoryDBStack(app, 'MemoryDBStack',
  vpc_stack.vpc,
  env=APP_ENV)
memorydb_stack.add_dependency(vpc_stack)

app.synth()
