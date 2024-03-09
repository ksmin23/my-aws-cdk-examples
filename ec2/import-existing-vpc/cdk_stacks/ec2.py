#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2
)
from constructs import Construct


class EC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_ssh_access = aws_ec2.SecurityGroup(self, "BastionHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for bastion host',
      security_group_name=f'bastion-host-sg-{self.stack_name.lower()}'
    )
    cdk.Tags.of(sg_ssh_access).add('Name', 'bastion-host')
    sg_ssh_access.add_ingress_rule(peer=aws_ec2.Peer.any_ipv4(), connection=aws_ec2.Port.tcp(22), description='ssh access')

    bastion_host = aws_ec2.BastionHostLinux(self, "BastionHost",
      vpc=vpc,
      instance_type=aws_ec2.InstanceType('t3.nano'),
      security_group=sg_ssh_access,
      subnet_selection=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )

    cdk.CfnOutput(self, 'BastionHostId',
      value=bastion_host.instance_id,
      export_name=f'{self.stack_name}-BastionHostId')
    cdk.CfnOutput(self, 'BastionHostPublicDNSName',
      value=bastion_host.instance_public_dns_name,
      export_name=f'{self.stack_name}-BastionHostPublicDNSName')
