#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_redshift,
  aws_secretsmanager,
)
from constructs import Construct


class RedshiftCfnStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_rs_client = aws_ec2.SecurityGroup(self, 'RedshiftClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redshift client',
      security_group_name=f'redshift-client-sg-{self.stack_name}'
    )
    cdk.Tags.of(sg_rs_client).add('Name', 'redshift-client-sg')

    sg_rs_cluster = aws_ec2.SecurityGroup(self, 'RedshiftClusterSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redshift cluster nodes',
      security_group_name=f'redshift-cluster-sg-{self.stack_name}'
    )
    sg_rs_cluster.add_ingress_rule(peer=sg_rs_client, connection=aws_ec2.Port.tcp(5439),
      description='redshift-client-sg')
    sg_rs_cluster.add_ingress_rule(peer=sg_rs_cluster, connection=aws_ec2.Port.all_tcp(),
      description='redshift-cluster-sg')
    cdk.Tags.of(sg_rs_cluster).add('Name', 'redshift-cluster-sg')

    secret_name = self.node.try_get_context('aws_secret_name')
    rs_admin_user_secret = aws_secretsmanager.Secret.from_secret_name_v2(self,
      'RedshiftAdminUserSecret',
      secret_name)

    cfn_redshift_cluster = aws_redshift.CfnCluster(self, "RedshiftCfnCluster",
      cluster_type="multi-node", # [single-node, multi-node]
      db_name="default_db",
      master_username=rs_admin_user_secret.secret_value_from_json("admin_username").unsafe_unwrap(),
      master_user_password=rs_admin_user_secret.secret_value_from_json("admin_user_password").unsafe_unwrap(),
      node_type="ra3.xlplus",
      allow_version_upgrade=False,
      aqua_configuration_status="auto",
      automated_snapshot_retention_period=1,
      availability_zone_relocation_status="disabled",
      classic=False, # The resize operation is using the elastic resize process.
      cluster_version="1.0",
      encrypted=True,
      enhanced_vpc_routing=True,
      number_of_nodes=2,
      preferred_maintenance_window="sun:03:00-sun:04:00",
      publicly_accessible=False,
      vpc_security_group_ids=[sg_rs_cluster.security_group_id]
    )
    cfn_redshift_cluster.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, 'RedshiftClusterEndpoint',
      value=f'{cfn_redshift_cluster.endpoint}',
      export_name=f'{self.stack_name}-ClusterEndpoint')
    cdk.CfnOutput(self, 'RedshiftSecretArn',
      value=f'{rs_admin_user_secret.secret_full_arn}',
      export_name=f'{self.stack_name}-SecretArn')
