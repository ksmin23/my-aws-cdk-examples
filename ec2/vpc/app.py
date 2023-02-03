#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2
)
from constructs import Construct

class VpcStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # The code that defines your stack goes here
    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    vpc = aws_ec2.Vpc(self, 'VpcStack',
      ip_addresses=aws_ec2.IpAddresses.cidr("10.0.0.0/21"),
      max_azs=3,

      # 'subnetConfiguration' specifies the "subnet groups" to create.
      # Every subnet group will have a subnet for each AZ, so this
      # configuration will create `2 groups × 3 AZs = 6` subnets.
      subnet_configuration=[
        {
          "cidrMask": 24,
          "name": "Public",
          "subnetType": aws_ec2.SubnetType.PUBLIC,
        },
        {
          "cidrMask": 24,
          "name": "Private",
          "subnetType": aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
        }
      ],
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    sg_ssh_access = aws_ec2.SecurityGroup(self, "BastionHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for bastion host',
      security_group_name='bastion-host-sg'
    )
    cdk.Tags.of(sg_ssh_access).add('Name', 'bastion-host-sg')
    sg_ssh_access.add_ingress_rule(peer=aws_ec2.Peer.any_ipv4(), connection=aws_ec2.Port.tcp(22), description='ssh access')

    bastion_host = aws_ec2.BastionHostLinux(self, "BastionHost",
      vpc=vpc,
      instance_type=aws_ec2.InstanceType('t3.nano'),
      security_group=sg_ssh_access,
      subnet_selection=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )

    cdk.CfnOutput(self, 'BastionHostId', value=bastion_host.instance_id, export_name='BastionHostId')
    cdk.CfnOutput(self, 'BastionHostPublicDNSName', value=bastion_host.instance_public_dns_name, export_name='BastionHostPublicDNSName')


app = cdk.App()
VpcStack(app, "vpc", env=cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
