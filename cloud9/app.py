#!/usr/bin/env python3
import os

from aws_cdk import (
  core as cdk,
  aws_ec2,
  aws_cloud9
)

class Cloud9Stack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For createing Amazon MWAA in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name
    )

    # vpc = aws_ec2.Vpc(self, "Cloud9VPC",
    #   max_azs=3,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )
    c9env = aws_cloud9.Ec2Environment(self, "Cloud9Env",
      vpc=vpc,
      subnet_selection=aws_ec2.SubnetSelection(
        subnet_type=aws_ec2.SubnetType.PUBLIC
      ),
      instance_type=aws_ec2.InstanceType("m5.large")
    )

    cdk.CfnOutput(self, "C9URL", value=c9env.ide_url)


app = cdk.App()
Cloud9Stack(app, "Cloud9Stack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
