#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_rds,
  aws_secretsmanager
)
from constructs import Construct


class AuroraMysqlServerlessV2ClusterStack(Stack):

  def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    db_cluster_name = self.node.try_get_context('db_cluster_name') or 'data-mart'

    sg_mysql_client = aws_ec2.SecurityGroup(self, 'MySQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql client',
      security_group_name=f'{db_cluster_name}-mysql-client-sg'
    )
    cdk.Tags.of(sg_mysql_client).add('Name', 'aurora_mysql-client-sg')

    sg_mysql_server = aws_ec2.SecurityGroup(self, 'MySQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql',
      security_group_name=f'{db_cluster_name}-mysql-server-sg'
    )
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_client, connection=aws_ec2.Port.tcp(3306),
      description='aurora_mysql-client-sg')
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_server, connection=aws_ec2.Port.all_tcp(),
      description='aurora_mysql-server-sg')

    # Adds an ingress rule which allows resources in the VPC's CIDR to access the database.
    sg_mysql_server.add_ingress_rule(
      peer=aws_ec2.Peer.ipv4(vpc.vpc_cidr_block),
      connection=aws_ec2.Port.tcp(3306),
      description="Allow inbound from resources in the VPC"
    )

    cdk.Tags.of(sg_mysql_server).add('Name', 'aurora_mysql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'MySQLSubnetGroup',
      description='subnet group for mysql',
      subnet_group_name=f'{db_cluster_name}-aurora-mysql',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    #XXX: Aurora MySQL version numbers and special versions
    # https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.Versions.html
    rds_engine = aws_rds.DatabaseClusterEngine.AURORA_MYSQL

    #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Parameters.Cluster
    rds_cluster_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLClusterParamGroup',
      engine=rds_engine,
      description=f'Custom cluster parameter group for MySQL',
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

    #XXX: In order to exclude punctuations when generating a password
    # use aws_secretsmanager.Secret instead of aws_rds.DatabaseSecret.
    # Othwerise, an error occurred such as:
    # "All characters of the desired type have been excluded"
    db_secret = aws_secretsmanager.Secret(self, "DatabaseSecret",
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "clusteradmin"}),
        generate_string_key="password",
        exclude_punctuation=True,
        password_length=8
      )
    )
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    db_cluster = aws_rds.ServerlessCluster(self, 'AuroraMySQLServerlessCluster',
      engine=rds_engine,
      credentials=rds_credentials, # A username of 'admin' (or 'postgres' for PostgreSQL) and SecretsManager-generated password
      parameter_group=rds_cluster_param_group,
      backup_retention=cdk.Duration.days(3),
      cluster_identifier=db_cluster_name,
      scaling=aws_rds.ServerlessScalingOptions(
        auto_pause=cdk.Duration.minutes(10),  # default is to pause after 5 minutes of idle time
        min_capacity=aws_rds.AuroraCapacityUnit.ACU_2,  # default is 2 Aurora capacity units (ACUs)
        max_capacity=aws_rds.AuroraCapacityUnit.ACU_16
      ),
      subnet_group=rds_subnet_group,
      security_groups=[sg_mysql_server],
      vpc=vpc,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
    )

    self.sg_mysql_client = sg_mysql_client
    self.database_secret = db_cluster.secret
    self.database = db_cluster

    cdk.CfnOutput(self, 'RDSClientSecurityGroupId', value=sg_mysql_client.security_group_id,
                  export_name=f'{self.stack_name}-RDSClientSecurityGroupId')
    cdk.CfnOutput(self, 'DBSecretName', value=db_cluster.secret.secret_name,
                  export_name=f'{self.stack_name}-DBSecretName')
    cdk.CfnOutput(self, 'DBClusterEndpoint', value=db_cluster.cluster_endpoint.socket_address,
                  export_name=f'{self.stack_name}-DBClusterEndpoint')
