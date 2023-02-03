#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_cloud9 as cloud9
)
from constructs import Construct

class Cloud9Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    C9_OWNER_NAME = cdk.CfnParameter(self, 'Cloud9OwnerName',
      type='String',
      description='Cloud9 Owner name'
    )

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context('vpc_name')
    # vpc = aws_ec2.Vpc.from_lookup(self, 'Cloud9VPC',
    #   is_default=True,
    #   vpc_name=vpc_name
    # )

    vpc = aws_ec2.Vpc(self, "Cloud9VPC",
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

    #XXX: AWS Cloud9 CloudFormation Guide
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloud9-environmentec2.html
    c9owner = aws_iam.User.from_user_name(self, "Cloud9Owner",
      C9_OWNER_NAME.value_as_string)

    c9env = cloud9.CfnEnvironmentEC2(self, "Cloud9Env",
      instance_type="m5.large",

      # the properties below are optional
      automatic_stop_time_minutes=30,
      connection_type="CONNECT_SSH", # [CONNECT_SSH, CONNECT_SSM]
      #image_id="amazonlinux-2-x86_64", # "amazonlinux-1-x86_64" | "amazonlinux-2-x86_64" | "ubuntu-18.04-x86_64"
      name="c9env",
      owner_arn=c9owner.user_arn,
      subnet_id=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PUBLIC).subnet_ids[0]
    )


app = cdk.App()
Cloud9Stack(app, "Cloud9Stack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
