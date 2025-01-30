#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ecs
)
from constructs import Construct


class ECSTaskStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, ecr_repositories, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Define ECS Task Definition
    self.task_definition = aws_ecs.Ec2TaskDefinition(self, "TaskDef",
      network_mode=aws_ecs.NetworkMode.AWS_VPC
    )

    # Add container to task definition
    repository = ecr_repositories['nginx']
    container = self.task_definition.add_container(
      "web",
      image=aws_ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
      cpu=100,
      memory_limit_mib=256
    )

    # Expose port 80
    port_mapping = aws_ecs.PortMapping(
      container_port=80,
      protocol=aws_ecs.Protocol.TCP
    )
    container.add_port_mappings(port_mapping)


    cdk.CfnOutput(self, 'TaskDefinitionArn',
      value=self.task_definition.task_definition_arn,
      export_name=f'{self.stack_name}-TaskDefinitionArn')
