#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  BastionHostStack
)


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'VpcStack',
  env=AWS_ENV
)

ec2_stack = BastionHostStack(app, 'BastionHostStack',
  vpc_stack.vpc,
  env=AWS_ENV
)
ec2_stack.add_dependency(vpc_stack)

app.synth()
