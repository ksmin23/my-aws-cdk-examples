#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  ECRStack,
  ApplicationLoadBalancerStack,
  ECSAlbFargateServiceStack,
  ECSClusterStack,
  ECSTaskStack,
  EFSStack,
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

alb_stack = ApplicationLoadBalancerStack(app, "FargateServiceWithEfsALBStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
alb_stack.add_dependency(vpc_stack)

ecs_cluster_stack = ECSClusterStack(app, "FargateServiceWithEfsECSClusterStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
ecs_cluster_stack.add_dependency(vpc_stack)

efs_stack = EFSStack(app, "FargateServiceWithEfsEFSStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
efs_stack.add_dependency(ecs_cluster_stack)

ecs_task_stack = ECSTaskStack(app, "FargateServiceWithEfsECSTaskStack",
  ecr_stack.repositories,
  efs_stack.efs_file_system,
  env=AWS_ENV
)
ecs_task_stack.add_dependency(efs_stack)

ecs_fargate_stack = ECSAlbFargateServiceStack(app, "FargateServiceWithEfsECSServiceStack",
  vpc_stack.vpc,
  ecs_cluster_stack.ecs_cluster,
  ecs_task_stack.ecs_task_definition,
  alb_stack.load_balancer,
  efs_stack.sg_efs_inbound,
  env=AWS_ENV
)
ecs_fargate_stack.add_dependency(ecs_task_stack)

app.synth()
