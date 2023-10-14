#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  DLAMIEC2InstanceStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "DLAMIVpcStack",
  env=AWS_ENV)

dlami_ec2_stack = DLAMIEC2InstanceStack(app, "DLAMIEC2InstanceStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
dlami_ec2_stack.add_dependency(vpc_stack)

app.synth()
