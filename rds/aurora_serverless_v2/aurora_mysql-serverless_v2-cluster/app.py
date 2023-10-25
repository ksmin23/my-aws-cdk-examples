#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  AuroraMysqlServerlessV2ClusterStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "AuroraMySQLServerlessV2ClusterVpcStack",
  env=AWS_ENV)

rds_stack = AuroraMysqlServerlessV2ClusterStack(app, "AuroraMysqlServerlessV2ClusterStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
rds_stack.add_dependency(vpc_stack)

app.synth()
