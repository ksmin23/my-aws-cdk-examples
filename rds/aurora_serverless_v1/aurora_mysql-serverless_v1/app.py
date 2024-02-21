#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  AuroraMysqlServerlessV1ClusterStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "AuroraMySQLServerlessV1ClusterVpcStack",
  env=AWS_ENV)

rds_stack = AuroraMysqlServerlessV1ClusterStack(app, "AuroraMysqlServerlessV1ClusterStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
rds_stack.add_dependency(vpc_stack)

app.synth()
