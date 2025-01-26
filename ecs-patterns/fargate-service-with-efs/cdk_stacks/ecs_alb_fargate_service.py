#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_ecs_patterns,
)

from constructs import Construct


class ECSAlbFargateServiceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc,
    ecs_cluster,
    ecs_task_definition,
    load_balancer,
    sg_efs_inbound,
    **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    service_name = self.node.try_get_context('ecs_service_name') or "cloudcmd"

    sg_fargate_service = aws_ec2.SecurityGroup(self, 'ECSFargateServiceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description="Allow inbound from VPC for ECS Fargate Service",
      security_group_name=f'{service_name}-ecs-service-sg'
    )
    sg_fargate_service.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(8000))
    cdk.Tags.of(sg_fargate_service).add('Name', 'fargate-service-with-efs')

    fargate_service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(self, "ALBFargateService",
      service_name=service_name,
      cluster=ecs_cluster,
      desired_count=2,
      min_healthy_percent=50,
      task_definition=ecs_task_definition,
      load_balancer=load_balancer,
      security_groups=[sg_fargate_service, sg_efs_inbound]
    )
    fargate_service.target_group.set_attribute('deregistration_delay.timeout_seconds', '30')
    cdk.Tags.of(fargate_service).add('Name', 'fargate-service-with-efs')


    cdk.CfnOutput(self, "LoadBalancerDNS",
      value=f'http://{fargate_service.load_balancer.load_balancer_dns_name}',
      export_name=f'{self.stack_name}-LoadBalancerDNS')
    cdk.CfnOutput(self, 'TaskDefinitionArn',
      value=ecs_task_definition.task_definition_arn,
      export_name=f'{self.stack_name}-TaskDefinitionArn')
