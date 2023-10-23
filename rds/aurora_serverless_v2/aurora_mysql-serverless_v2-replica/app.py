#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  AuroraMySQLwithServerlessV2ReplicaStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "AuroraMySQLServerlessV2ReplicaVpcStack",
    env=AWS_ENV)

rds_stack = AuroraMySQLwithServerlessV2ReplicaStack(app, "AuroraMySQLServerlessV2RDSStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
rds_stack.add_dependency(vpc_stack)

app.synth()
