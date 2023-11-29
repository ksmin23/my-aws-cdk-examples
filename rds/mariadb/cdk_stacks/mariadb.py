#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_logs,
  aws_rds,
  aws_secretsmanager
)
from constructs import Construct

class MariaDBStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_mariadb_client = aws_ec2.SecurityGroup(self, 'MariaDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mariadb client',
      security_group_name=f'mariadb-client-sg-{self.stack_name}'
    )
    cdk.Tags.of(sg_mariadb_client).add('Name', 'mariadb-client-sg')

    sg_mariadb_server = aws_ec2.SecurityGroup(self, 'MariaDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mariadb',
      security_group_name=f'mariadb-server-sg-{self.stack_name}'
    )
    sg_mariadb_server.add_ingress_rule(peer=sg_mariadb_client, connection=aws_ec2.Port.tcp(3306),
      description='mariadb-client-sg')
    sg_mariadb_server.add_ingress_rule(peer=sg_mariadb_server, connection=aws_ec2.Port.all_tcp(),
      description='mariadb-server-sg')
    cdk.Tags.of(sg_mariadb_server).add('Name', 'mariadb-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'MariaDBSubnetGroup',
      description='subnet group for mariadb',
      subnet_group_name='rds-mariadb',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    rds_param_group = aws_rds.ParameterGroup(self, 'MariaDBParamGroup',
      engine=aws_rds.DatabaseInstanceEngine.maria_db(version=aws_rds.MariaDbEngineVersion.VER_10_6_8),
      description='Custom parameter group for mariadb10.6',
      parameters={
        'innodb_flush_log_at_trx_commit': '2',
        'slow_query_log': '1',
        'tx_isolation': 'READ-COMMITTED',
        'wait_timeout': '300',
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
    db_secret = aws_secretsmanager.Secret(self, 'DatabaseSecret',
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "admin"}),
        generate_string_key="password",
        exclude_punctuation=True,
        password_length=8
      )
    )
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    rds_engine = aws_rds.DatabaseInstanceEngine.MARIADB
    primary_instance = aws_rds.DatabaseInstance(self, "MariaDBPrimary",
      engine=rds_engine,
      credentials=rds_credentials,
      instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.LARGE),
      vpc=vpc,
      auto_minor_version_upgrade=False,
      backup_retention=cdk.Duration.days(3),
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      enable_performance_insights=True,
      # multi_az=False,
      parameter_group=rds_param_group,
      #XXX: The backup window and maintenance window must not overlap.
      preferred_backup_window='17:00-18:00', # hh24:mi-hh24:mi
      preferred_maintenance_window='Sun:18:00-Sun:19:00', # ddd:hh24:mi-ddd:hh24:mi
      removal_policy=cdk.RemovalPolicy.SNAPSHOT,
      security_groups=[sg_mariadb_server],
      subnet_group=rds_subnet_group
    )

    replica_instance = aws_rds.DatabaseInstanceReadReplica(self, "MariaDBReadReplica",
      source_database_instance=primary_instance,
      instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.LARGE),
      vpc=vpc,
      auto_minor_version_upgrade=False,
      backup_retention=cdk.Duration.days(3),
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      enable_performance_insights=True,
      # multi_az=False,
      parameter_group=rds_param_group,
      #XXX: The backup window and maintenance window must not overlap.
      preferred_backup_window='16:30-17:30', # hh24:mi-hh24:mi
      preferred_maintenance_window='Sun:17:30-Sun:18:30', #ddd:hh24:mi-ddd:hh24:mi
      removal_policy=cdk.RemovalPolicy.SNAPSHOT,
      security_groups=[sg_mariadb_server],
      subnet_group=rds_subnet_group
    )


    cdk.CfnOutput(self, 'DBPrimaryEndpoint', value=primary_instance.db_instance_endpoint_address,
      export_name=f'{self.stack_name}-DBPrimaryEndpoint')
    cdk.CfnOutput(self, 'DBReplicaEndpoint', value=replica_instance.db_instance_endpoint_address,
      export_name=f'{self.stack_name}-DBReplicaEndpoint')
    cdk.CfnOutput(self, 'DBInstanceEndpointPort', value=primary_instance.db_instance_endpoint_port,
      export_name=f'{self.stack_name}-DBInstanceEndpointPort')
    cdk.CfnOutput(self, 'RDSClientSecurityGroupId', value=sg_mariadb_client.security_group_id,
      export_name=f'{self.stack_name}-RDSClientSecurityGroupId')
    cdk.CfnOutput(self, 'DBSecretName', value=primary_instance.secret.secret_name,
      export_name=f'{self.stack_name}-DBSecretName')