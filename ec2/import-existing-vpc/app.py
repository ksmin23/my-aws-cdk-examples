#!/usr/bin/env python3

import os

from aws_cdk import (
  core,
  aws_ec2,
  aws_iam
)


class EC2InstanceStack(core.Stack):

  def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    # The code that defines your stack goes here
    vpc_name = self.node.try_get_context("vpc_name")
    vpc = aws_ec2.Vpc.from_lookup(self, "EC2InstanceVPC",
      is_default=True,
      vpc_name=vpc_name)

    sg_ssh_access = aws_ec2.SecurityGroup(self, "BastionHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for bastion host',
      security_group_name='bastion-host-sg'
    )
    core.Tag.of(sg_ssh_access).add('Name', 'bastion-host')
    sg_ssh_access.add_ingress_rule(peer=aws_ec2.Peer.any_ipv4(), connection=aws_ec2.Port.tcp(22), description='ssh access')

    bastion_host = aws_ec2.BastionHostLinux(self, "BastionHost",
      vpc=vpc,
      instance_type=aws_ec2.InstanceType('t3.nano'),
      security_group=sg_ssh_access,
      subnet_selection=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )


app = core.App()

EC2InstanceStack(app, "EC2Instance", env=core.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
