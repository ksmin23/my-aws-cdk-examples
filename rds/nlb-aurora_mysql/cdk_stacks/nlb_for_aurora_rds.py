#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import socket
from typing import List

import boto3
import botocore

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_elasticloadbalancingv2 as aws_elbv2,
  aws_elasticloadbalancingv2_targets as aws_elbv2_targets,
)
from constructs import Construct


def get_cfn_outputs(stack_name: str, region_name: str) -> List:
  cfn = boto3.client('cloudformation', region_name=region_name)
  outputs = {}
  try:
    for output in cfn.describe_stacks(StackName=stack_name)['Stacks'][0]['Outputs']:
      outputs[output['OutputKey']] = output['OutputValue']
  except botocore.exceptions.ClientError as _:
    pass
  return outputs


class NLBforAuroraRDSStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, db_cluster, sg_rds_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    cfn_outputs = get_cfn_outputs(stack_name=db_cluster.stack.stack_name, region_name=db_cluster.stack.region)
    db_cluster_endpoint = cfn_outputs.get('DBClusterEndpoint', None)
    if not db_cluster_endpoint:
      db_cluster_endpoint_hostname, db_cluster_endpoint_port = (None, 3306)
    else:
      db_cluster_endpoint_hostname, db_cluster_endpoint_port = db_cluster_endpoint.rsplit(':', 1)
    port = int(db_cluster_endpoint_port)

    sg_nlb = aws_ec2.SecurityGroup(self, 'NLBSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for NLB',
      security_group_name=f'{self.stack_name}-nlb-sg'
    )
    sg_nlb.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(port),
      description='nlb-sg')
    cdk.Tags.of(sg_nlb).add('Name', 'nlb-sg')

    self.nlb = aws_elbv2.NetworkLoadBalancer(self, "NLB",
      vpc=vpc,
      security_groups=[sg_rds_client, sg_nlb],
      internet_facing=False
    )

    listener = self.nlb.add_listener("Listener",
      port=port
    )

    ip_address = socket.gethostbyname(db_cluster_endpoint_hostname) if db_cluster_endpoint_hostname else None
    ip_targets = aws_elbv2_targets.IpTarget(ip_address) if ip_address else None
    self.target_group = listener.add_targets("AuroraRDSTargets",
      port=port,
      targets=ip_targets,
      deregistration_delay=cdk.Duration.seconds(0),
      health_check=aws_elbv2.HealthCheck(
        enabled=True,
        healthy_threshold_count=3,
        interval=cdk.Duration.seconds(10),
        port=f"{port}",
        protocol=aws_elbv2.Protocol.TCP,
        timeout=cdk.Duration.seconds(10),
        unhealthy_threshold_count=2
      )
    )


    cdk.CfnOutput(self, 'NlbDNSName', value=self.nlb.load_balancer_dns_name,
      export_name=f'{self.stack_name}-NlbDNSName')
