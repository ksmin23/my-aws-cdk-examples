#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_msk
)
from constructs import Construct


class MSKServerlessStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    msk_cluster_name = self.node.try_get_context("msk_cluster_name")

    MSK_CLIENT_SG_NAME = f'msk-client-sg-{msk_cluster_name}'
    sg_msk_client = aws_ec2.SecurityGroup(self, 'KafkaClientSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK client',
      security_group_name=MSK_CLIENT_SG_NAME
    )
    cdk.Tags.of(sg_msk_client).add('Name', MSK_CLIENT_SG_NAME)

    MSK_CLUSTER_SG_NAME = f'msk-cluster-sg-{msk_cluster_name}'
    sg_msk_cluster = aws_ec2.SecurityGroup(self, 'MSKSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK Cluster',
      security_group_name=MSK_CLUSTER_SG_NAME
    )
    sg_msk_cluster.add_ingress_rule(peer=sg_msk_client, connection=aws_ec2.Port.tcp(9098),
      description='msk client security group')
    cdk.Tags.of(sg_msk_cluster).add('Name', MSK_CLUSTER_SG_NAME)

    msk_serverless_cluster = aws_msk.CfnServerlessCluster(self, "MSKServerlessCfnCluster",
      #XXX: A serverless cluster must use SASL/IAM authentication
      client_authentication=aws_msk.CfnServerlessCluster.ClientAuthenticationProperty(
        sasl=aws_msk.CfnServerlessCluster.SaslProperty(
          iam=aws_msk.CfnServerlessCluster.IamProperty(
            enabled=True
          )
        )
      ),
      cluster_name=msk_cluster_name,
      vpc_configs=[aws_msk.CfnServerlessCluster.VpcConfigProperty(
        subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
        security_groups=[sg_msk_client.security_group_id, sg_msk_cluster.security_group_id]
      )]
    )

    self.sg_msk_client = sg_msk_client
    self.msk_cluster_name = msk_serverless_cluster.cluster_name
    self.msk_cluster_arn = msk_serverless_cluster.attr_arn

    cdk.CfnOutput(self, 'KafkaSecurityGroupID', value=sg_msk_cluster.security_group_id,
      export_name=f'{self.stack_name}-ClusterSecurityGroupID')
    cdk.CfnOutput(self, 'KafkaClientSecurityGroupID', value=self.sg_msk_client.security_group_id,
      export_name=f'{self.stack_name}-ClientSecurityGroupID')
    cdk.CfnOutput(self, 'KafkaClusterName', value=self.msk_cluster_name,
      export_name=f'{self.stack_name}-KafkaClusterName')
    cdk.CfnOutput(self, 'KafkaClusterARN', value=self.msk_cluster_arn,
      export_name=f'{self.stack_name}-KafkaClusterARN')
