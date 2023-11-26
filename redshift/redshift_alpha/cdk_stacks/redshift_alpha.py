#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_redshift_alpha
)
from constructs import Construct


class RedshiftStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_rs_client = aws_ec2.SecurityGroup(self, 'RedshiftClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redshift client',
      security_group_name='redshift-client-sg'
    )
    cdk.Tags.of(sg_rs_client).add('Name', 'redshift-client-sg')

    sg_rs_cluster = aws_ec2.SecurityGroup(self, 'RedshiftClusterSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redshift cluster nodes',
      security_group_name='redshift-cluster-sg'
    )
    sg_rs_cluster.add_ingress_rule(peer=sg_rs_client, connection=aws_ec2.Port.tcp(5439),
      description='redshift-client-sg')
    sg_rs_cluster.add_ingress_rule(peer=sg_rs_cluster, connection=aws_ec2.Port.all_tcp(),
      description='redshift-cluster-sg')
    cdk.Tags.of(sg_rs_cluster).add('Name', 'redshift-cluster-sg')

    redshift_cluster = aws_redshift_alpha.Cluster(self, "Redshift",
      master_user=aws_redshift_alpha.Login(
        master_username="admin"
      ),
      vpc=vpc,
      enhanced_vpc_routing=True,
      node_type=aws_redshift_alpha.NodeType.RA3_XLPLUS,
      preferred_maintenance_window="Sun:03:00-Sun:04:00",
      security_groups=[sg_rs_cluster],
      removal_policy=cdk.RemovalPolicy.DESTROY
    )
    redshift_cluster.add_to_parameter_group("enable_user_activity_logging", "true")

    cdk.CfnOutput(self, 'RedshiftClusterEndpoint',
      value=f'{redshift_cluster.cluster_endpoint.hostname}:{redshift_cluster.cluster_endpoint.port}',
      export_name=f'{self.stack_name}-ClusterEndpoint')
    cdk.CfnOutput(self, 'RedshiftSecretArn',
      value=f'{redshift_cluster.secret.secret_arn}',
      export_name=f'{self.stack_name}-SecretArn')