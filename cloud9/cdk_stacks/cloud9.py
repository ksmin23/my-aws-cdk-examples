#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_cloud9 as cloud9
)
from constructs import Construct


class Cloud9Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    C9_OWNER_NAME = self.node.try_get_context('Cloud9OwnerName')

    #XXX: AWS Cloud9 CloudFormation Guide
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloud9-environmentec2.html
    c9owner = aws_iam.User.from_user_name(self, "Cloud9Owner",
      C9_OWNER_NAME)

    C9_CONFIG = self.node.try_get_context('cloud9')

    c9env = cloud9.CfnEnvironmentEC2(self, "Cloud9Env",
      instance_type=C9_CONFIG['instance_type'],

      # the properties below are optional
      automatic_stop_time_minutes=30,
      connection_type="CONNECT_SSH", # [CONNECT_SSH, CONNECT_SSM]
      image_id=C9_CONFIG['image_id'], # "amazonlinux-2-x86_64" | "ubuntu-22.04-x86_64"
      name=C9_CONFIG['name'],
      owner_arn=c9owner.user_arn,
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PUBLIC).subnet_ids[0]
    )

    cdk.CfnOutput(self, 'Cloud9Name', value=c9env.name,
      export_name=f'{self.stack_name}-Name')
    cdk.CfnOutput(self, 'Cloud9ImageId', value=c9env.image_id,
      export_name=f'{self.stack_name}-ImageId')