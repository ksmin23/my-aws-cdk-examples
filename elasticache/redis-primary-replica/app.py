#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
    VpcStack,
    RedisClusterStack
)


APP_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'RedisPrimaryRelplicaVPCStack',
  env=APP_ENV)

redis_cluster_stack = RedisClusterStack(app, 'RedisPrimaryRelplicaClusterStack',
  vpc_stack.vpc,
  env=APP_ENV
)
redis_cluster_stack.add_dependency(vpc_stack)

app.synth()
