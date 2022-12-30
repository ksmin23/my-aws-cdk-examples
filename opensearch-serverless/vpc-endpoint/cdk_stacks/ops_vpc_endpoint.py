#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_opensearchserverless as aws_opss
)
from constructs import Construct


class OpssVpcEndpointStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, opensearch_cluster_sg, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    cfn_vpc_endpoint = aws_opss.CfnVpcEndpoint(self, "OpssVpcEndpoint",
      name="opensearch-vpc-endpoint", # Expected maxLength: 32
      vpc_id=vpc.vpc_id,
      security_group_ids=[opensearch_cluster_sg.security_group_id],
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
    )
    cfn_vpc_endpoint.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
    self.vpc_endpoint_id = cfn_vpc_endpoint.ref

    cdk.CfnOutput(self, f'{self.stack_name}-VpcEndpointId', value=self.vpc_endpoint_id)
