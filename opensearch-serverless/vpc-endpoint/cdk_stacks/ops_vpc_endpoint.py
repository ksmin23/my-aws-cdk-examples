#!/usr/bin/env python3
import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_opensearchserverless as aws_opss
)
from constructs import Construct


class OpssVpcEndpointStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_use_opensearch = aws_ec2.SecurityGroup(self, "OpenSearchClientSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch client',
      security_group_name='use-opensearch-cluster-sg'
    )
    cdk.Tags.of(sg_use_opensearch).add('Name', 'use-opensearch-cluster-sg')

    sg_opensearch_cluster = aws_ec2.SecurityGroup(self, "OpenSearchSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an opensearch cluster',
      security_group_name='opensearch-cluster-sg'
    )
    cdk.Tags.of(sg_opensearch_cluster).add('Name', 'opensearch-cluster-sg')
    self.opensearch_client_sg = sg_use_opensearch

    sg_opensearch_cluster.add_ingress_rule(peer=sg_opensearch_cluster, connection=aws_ec2.Port.all_tcp(), description='opensearch-cluster-sg')

    sg_opensearch_cluster.add_ingress_rule(peer=sg_use_opensearch, connection=aws_ec2.Port.tcp(443), description='use-opensearch-cluster-sg')
    sg_opensearch_cluster.add_ingress_rule(peer=sg_use_opensearch, connection=aws_ec2.Port.tcp_range(9200, 9300), description='use-opensearch-cluster-sg')

    cfn_vpc_endpoint = aws_opss.CfnVpcEndpoint(self, "OpssVpcEndpoint",
      name="opensearch-vpc-endpoint", # Expected maxLength: 32
      vpc_id=vpc.vpc_id,
      security_group_ids=[sg_opensearch_cluster.security_group_id],
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
    )
    cfn_vpc_endpoint.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
    self.vpc_endpoint_id = cfn_vpc_endpoint.ref

    cdk.CfnOutput(self, f'{self.stack_name}-VpcEndpointId', value=self.vpc_endpoint_id)
