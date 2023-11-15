#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,

  aws_ec2,
  aws_ecs,
  aws_ecs_patterns,
)

from constructs import Construct


class ECSAlbFargateServiceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc, sg_rds_client, ecs_cluster, ecs_task_definition,
    **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    service_name = self.node.try_get_context('ecs_service_name') or "streamlit-alb-service"

    fargate_service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(self, "ALBFargateService",
      service_name=service_name,
      cluster=ecs_cluster,
      task_definition=ecs_task_definition
    )

    # Setup security group
    fargate_service.service.connections.security_groups[0].add_ingress_rule(
      peer=aws_ec2.Peer.ipv4(vpc.vpc_cidr_block),
      connection=aws_ec2.Port.tcp(8501),
      description="Allow inbound from VPC for ECS Fargate Service",
    )

    fargate_service.load_balancer.add_security_group(sg_rds_client)

    # Setup autoscaling policy
    scalable_target = fargate_service.service.auto_scale_task_count(max_capacity=2)
    scalable_target.scale_on_cpu_utilization(
      id="Autoscaling",
      target_utilization_percent=70,
      scale_in_cooldown=cdk.Duration.seconds(60),
      scale_out_cooldown=cdk.Duration.seconds(60),
    )

    cdk.CfnOutput(self, "LoadBalancerDNS",
      value=f'http://{fargate_service.load_balancer.load_balancer_dns_name}',
      export_name=f'{self.stack_name}-LoadBalancerDNS')