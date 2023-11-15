#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  AuroraMysqlServerlessV2ClusterStack,
  BastionHostEC2InstanceStack,
  ECSNlbFargateServiceStack,
  ECSClusterStack,
  ECSTaskStack,
  VpcStack
)

AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "ECSNlbFargateServiceVpcStack",
    env=AWS_ENV)

rds_stack = AuroraMysqlServerlessV2ClusterStack(app, "AuroraMySQLServerlessV2Stack",
  vpc_stack.vpc,
  env=AWS_ENV
)
rds_stack.add_dependency(vpc_stack)

bastion_host = BastionHostEC2InstanceStack(app, "BastionHostStack",
  vpc_stack.vpc,
  rds_stack.sg_mysql_client,
  env=AWS_ENV
)
bastion_host.add_dependency(rds_stack)

ecs_cluster_stack = ECSClusterStack(app, "ECSClusterStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
ecs_cluster_stack.add_dependency(bastion_host)

ecs_task_stack = ECSTaskStack(app, "ECSTaskStack",
  rds_stack.database_secret,
  env=AWS_ENV
)
ecs_task_stack.add_dependency(ecs_cluster_stack)

ecs_fargate_stack = ECSNlbFargateServiceStack(app, "ECSNlbFargateServiceStack",
  vpc_stack.vpc,
  ecs_cluster_stack.ecs_cluster,
  ecs_task_stack.ecs_task_definition,
  env=AWS_ENV
)
ecs_fargate_stack.add_dependency(ecs_task_stack)

app.synth()