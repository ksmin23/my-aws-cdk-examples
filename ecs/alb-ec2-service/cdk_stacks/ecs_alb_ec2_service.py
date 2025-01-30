#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_ecs,
  aws_elasticloadbalancingv2 as elbv2
)
from constructs import Construct


class ECSAlbEc2ServiceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, cluster, task_definition, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Create a security group that allows HTTP traffic on port 80 for our
    # containers without modifying the security group on the instance
    service_sg = aws_ec2.SecurityGroup(self, "Ec2ServiceSG",
      vpc=vpc,
      allow_all_outbound=True
    )

    service_sg.add_ingress_rule(
      peer=aws_ec2.Peer.any_ipv4(),
      connection=aws_ec2.Port.tcp(80)
    )

    # Create ECS Service using the task definition
    service = aws_ecs.Ec2Service(self, "Ec2Service",
      cluster=cluster,
      task_definition=task_definition,
      security_groups=[service_sg],
      min_healthy_percent=50
    )

    # Create Application Load Balancer
    # Internet-facing ALB in the VPC
    lb = elbv2.ApplicationLoadBalancer(self, "LB",
      vpc=vpc,
      internet_facing=True
    )

    # Add ALB listener on port 80
    listener = lb.add_listener(
      "PublicListener",
      protocol=elbv2.ApplicationProtocol.HTTP
    )

    # Attach ALB to ECS Service with health check configuration
    listener.add_targets(
      "ECS",
      protocol=elbv2.ApplicationProtocol.HTTP,
      deregistration_delay=cdk.Duration.seconds(30), # draining interval
      targets=[service],
      health_check=elbv2.HealthCheck(
        interval=cdk.Duration.seconds(30),
        path="/",
        timeout=cdk.Duration.seconds(5),
        healthy_http_codes='200',
        healthy_threshold_count=5,
        unhealthy_threshold_count=2
      )
    )


    cdk.CfnOutput(self, 'LoadBalancerDNS',
      value=f"http://{lb.load_balancer_dns_name}",
      export_name=f'{self.stack_name}-LoadBalancerDNS')
