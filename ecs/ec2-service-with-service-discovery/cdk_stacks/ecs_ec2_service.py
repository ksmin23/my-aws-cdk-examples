#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_ecs
)
from constructs import Construct


class ECSEc2ServiceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc,
    cluster,
    task_definition,
    cloud_map_service,
    **kwargs) -> None:

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

    service.associate_cloud_map_service(
      service=cloud_map_service,
      container_port=service.task_definition.default_container.container_port)

    service_internal_url = f"http://{cloud_map_service.service_name}.{cloud_map_service.namespace.namespace_name}:80"


    cdk.CfnOutput(self, "ServiceInternalUrl",
      value=service_internal_url,
      export_name=f'{self.stack_name}-ServiceInternalUrl')
