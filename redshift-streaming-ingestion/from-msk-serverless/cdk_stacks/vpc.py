#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
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
    if str(os.environ.get('USE_DEFAULT_VPC', 'false')).lower() == 'true':
      vpc_name = self.node.try_get_context('vpc_name') or "default"
      self.vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
        is_default=True,
        vpc_name=vpc_name
      )
    else:
      #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
      #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
      self.vpc = aws_ec2.Vpc(self, "RedshiftStreamingStackVPC",
        max_azs=3,
        gateway_endpoints={
          "S3": aws_ec2.GatewayVpcEndpointOptions(
            service=aws_ec2.GatewayVpcEndpointAwsService.S3
          )
        }
      )


    cdk.CfnOutput(self, 'VPCID', value=self.vpc.vpc_id,
      export_name=f'{self.stack_name}-VPCID')
