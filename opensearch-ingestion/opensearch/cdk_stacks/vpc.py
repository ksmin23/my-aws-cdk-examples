#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
)
from constructs import Construct


class VpcStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context("vpc_name") or "default"
    # vpc = aws_ec2.Vpc.from_lookup(self, "OpenSearchDomainVpc",
    #   is_default=True,
    #   vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    vpc = aws_ec2.Vpc(self, "OpenSearchDomainVpc",
      max_azs=3,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    self.vpc = vpc

    #XXX: The Name field of every Export member must be specified and
    # consist only of alphanumeric characters,colons, or hyphens.
    cdk.CfnOutput(self, '{}_VPCID'.format(self.stack_name), value=self.vpc.vpc_id,
      export_name='{}-VPCID'.format(self.stack_name))

