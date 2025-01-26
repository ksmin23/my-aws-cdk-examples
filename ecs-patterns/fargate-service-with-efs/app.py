#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  ECRStack,
  ECSAlbFargateServiceWithEfsStack,
  ECSClusterStack,
  VpcStack
)

AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

ecr_stack = ECRStack(app, "FargateServiceWithEfsECRStack",
  env=AWS_ENV
)

vpc_stack = VpcStack(app, "FargateServiceWithEfsVpcStack",
  env=AWS_ENV
)
vpc_stack.add_dependency(ecr_stack)

ecs_cluster_stack = ECSClusterStack(app, "FargateServiceWithEfsECSClusterStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
ecs_cluster_stack.add_dependency(vpc_stack)

ecs_fargate_stack = ECSAlbFargateServiceWithEfsStack(app, "FargateServiceWithEfsECSServiceStack",
  vpc_stack.vpc,
  ecs_cluster_stack.ecs_cluster,
  ecr_stack.repositories,
  env=AWS_ENV
)
ecs_fargate_stack.add_dependency(ecs_cluster_stack)

app.synth()
