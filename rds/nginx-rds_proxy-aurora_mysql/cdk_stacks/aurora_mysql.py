#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_logs,
  aws_rds,
  aws_secretsmanager
)
from constructs import Construct


class AuroraMysqlStack(Stack):

  def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    sg_use_mysql = aws_ec2.SecurityGroup(self, 'MySQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql client',
      security_group_name='default-mysql-client-sg'
    )
    cdk.Tags.of(sg_use_mysql).add('Name', 'default-mysql-client-sg')

    sg_mysql_server = aws_ec2.SecurityGroup(self, 'MySQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql',
      security_group_name='default-mysql-server-sg'
    )
    sg_mysql_server.add_ingress_rule(peer=sg_use_mysql, connection=aws_ec2.Port.tcp(3306),
      description='default-mysql-client-sg')
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_server, connection=aws_ec2.Port.all_tcp(),
      description='default-mysql-server-sg')
    cdk.Tags.of(sg_mysql_server).add('Name', 'default-mysql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'MySQLSubnetGroup',
      description='subnet group for mysql',
      subnet_group_name='aurora-mysql',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    rds_engine = aws_rds.DatabaseClusterEngine.aurora_mysql(version=aws_rds.AuroraMysqlEngineVersion.VER_3_01_0)

    #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Parameters.Cluster
    rds_cluster_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLClusterParamGroup',
      engine=rds_engine,
      description='Custom cluster parameter group for aurora-mysql8.x',
      parameters={
        # For Aurora MySQL version 3, Aurora always uses the default value of 1.
        # 'innodb_flush_log_at_trx_commit': '2',
        'slow_query_log': '1',
        # Removed from Aurora MySQL version 3.
        # 'tx_isolation': 'READ-COMMITTED',
        'wait_timeout': '300',
        'character-set-client-handshake': '0',
        'character_set_server': 'utf8mb4',
        'collation_server': 'utf8mb4_unicode_ci',
        'init_connect': 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci',
        #'binlog_format': 'ROW' #XXX: Turn on binlog
      }
    )

    #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Parameters.Instance
    rds_db_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLDBParamGroup',
      engine=rds_engine,
      description='Custom parameter group for aurora-mysql8.x',
      parameters={
        'slow_query_log': '1',
        # Removed from Aurora MySQL version 3.
        # 'tx_isolation': 'READ-COMMITTED',
        'wait_timeout': '300',
        'init_connect': 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci'
      }
    )

    db_cluster_name = self.node.try_get_context('db_cluster_name')
    #XXX: aws_rds.Credentials.from_username(username, ...) can not be given user specific Secret name
    # therefore, first create Secret and then use it to create database
    db_secret_name = self.node.try_get_context('db_secret_name')
    #XXX: arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
    db_secret_arn = 'arn:aws:secretsmanager:{region}:{account}:secret:{resource_name}'.format(
      region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID, resource_name=db_secret_name)
    db_secret = aws_secretsmanager.Secret.from_secret_partial_arn(self, 'DBSecretFromArn', db_secret_arn)
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    db_cluster = aws_rds.DatabaseCluster(self, 'Database',
      engine=rds_engine,
      credentials=rds_credentials, # A username of 'admin' (or 'postgres' for PostgreSQL) and SecretsManager-generated password
      writer=aws_rds.ClusterInstance.provisioned("writer",
        instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
        parameter_group=rds_db_param_group,
        auto_minor_version_upgrade=False,
      ),
      readers=[
        aws_rds.ClusterInstance.provisioned("reader",
          instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
          parameter_group=rds_db_param_group,
          auto_minor_version_upgrade=False
        )
      ],
      parameter_group=rds_cluster_param_group,
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      cluster_identifier=db_cluster_name,
      subnet_group=rds_subnet_group,
      backup=aws_rds.BackupProps(
        retention=cdk.Duration.days(3),
        preferred_window="03:00-04:00"
      ),
      security_groups=[sg_mysql_server],
      vpc=vpc,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
    )

    self.sg_rds_client = sg_use_mysql

    cdk.CfnOutput(self, 'DBClusterEndpoint', value=db_cluster.cluster_endpoint.socket_address, export_name='DBClusterEndpoint')
    cdk.CfnOutput(self, 'DBClusterReadEndpoint', value=db_cluster.cluster_read_endpoint.socket_address, export_name='DBClusterReadEndpoint')
