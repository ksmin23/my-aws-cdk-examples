#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  ECRStack,
  ECSClusterStack,
  ECSTaskStack,
  ECSAlbEc2ServiceStack,
  VpcStack
)

AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

ecr_stack = ECRStack(app, "EC2ServiceECRStack",
  env=AWS_ENV
)

vpc_stack = VpcStack(app, "EC2ServiceVpcStack",
  env=AWS_ENV
)
vpc_stack.add_dependency(ecr_stack)

ecs_cluster_stack = ECSClusterStack(app, "EC2ServiceECSClusterStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
ecs_cluster_stack.add_dependency(vpc_stack)

ecs_task_stack = ECSTaskStack(app, "EC2ServiceECSTaskStack",
  ecr_stack.repositories,
  env=AWS_ENV
)
ecs_task_stack.add_dependency(ecs_cluster_stack)

ec2_service_stack = ECSAlbEc2ServiceStack(app, "EC2ALBServiceECSServiceStack",
  vpc=vpc_stack.vpc,
  cluster=ecs_cluster_stack.ecs_cluster,
  task_definition=ecs_task_stack.task_definition,
  env=AWS_ENV
)
ec2_service_stack.add_dependency(ecs_task_stack)

app.synth()
