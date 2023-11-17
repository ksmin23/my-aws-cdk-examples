#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_docdb
)
from constructs import Construct


class DocumentdbStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    docdb_cluster_name = self.node.try_get_context('docdb_cluster_name') or self.stack_name

    sg_docdb_client = aws_ec2.SecurityGroup(self, 'DocDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for documentdb client',
      security_group_name=f'use-docdb-sg-{docdb_cluster_name}'
    )
    cdk.Tags.of(sg_docdb_client).add('Name', 'docdb-client-sg')

    sg_docdb_server = aws_ec2.SecurityGroup(self, 'DocDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for documentdb',
      security_group_name=f'server-sg-docdb-{docdb_cluster_name}'
    )
    sg_docdb_server.add_ingress_rule(peer=sg_docdb_client, connection=aws_ec2.Port.tcp(27017),
      description='docdb-client-sg')
    cdk.Tags.of(sg_docdb_server).add('Name', 'docdb-server-sg')

    docdb_cluster = aws_docdb.DatabaseCluster(self, 'DocDB',
      db_cluster_name=docdb_cluster_name,
      master_user=aws_docdb.Login(
        username='docdbuser'
      ),
      # instance_type=aws_ec2.InstanceType('r5.xlarge'),
      instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.MEMORY5, aws_ec2.InstanceSize.LARGE),
      instances=3,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc,
      security_group=sg_docdb_server,
      preferred_maintenance_window='sun:18:00-sun:18:30',
      enable_performance_insights=True,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    #[Warning at /docdb-sm/Database/RotationSingleUser/SecurityGroup] Ignoring Egress rule since 'allowAllOutbound' is set to true;
    # To add customize rules, set allowAllOutbound=false on the SecurityGroup
    # docdb_cluster.add_rotation_single_user()

    self.sg_docdb_client = sg_docdb_client
    self.docdb_cluster = docdb_cluster

    cdk.CfnOutput(self, 'DocumentDBClusterName', value=self.docdb_cluster.cluster_identifier,
      export_name=f'{self.stack_name}-DocumentDBClusterName')
    cdk.CfnOutput(self, 'DocumentDBCluster', value=self.docdb_cluster.cluster_endpoint.socket_address,
      export_name=f'{self.stack_name}-DocumentDBCluster')
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_secretsmanager/README.html
    # secret_arn="arn:aws:secretsmanager:<region>:<account-id-number>:secret:<secret-name>-<random-6-characters>",
    cdk.CfnOutput(self, 'DocDBSecret', value=self.docdb_cluster.secret.secret_name,
      export_name=f'{self.stack_name}-DocDBSecret')
