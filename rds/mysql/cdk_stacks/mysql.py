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


class MysqlStack(Stack):

  def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    db_instance_name = self.node.try_get_context('rds_instance_name') or 'demo-mysql'

    self.sg_mysql_client = aws_ec2.SecurityGroup(self, 'MySQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql client',
      security_group_name=f'{db_instance_name}-mysql-client-sg'
    )
    cdk.Tags.of(self.sg_mysql_client).add('Name', 'mysql-client-sg')

    sg_mysql_server = aws_ec2.SecurityGroup(self, 'MySQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql',
      security_group_name=f'{db_instance_name}-mysql-server-sg'
    )
    sg_mysql_server.add_ingress_rule(peer=self.sg_mysql_client, connection=aws_ec2.Port.tcp(3306),
      description='mysql-client-sg')
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_server, connection=aws_ec2.Port.all_tcp(),
      description='mysql-server-sg')
    cdk.Tags.of(sg_mysql_server).add('Name', 'mysql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'MySQLSubnetGroup',
      description='subnet group for mysql',
      subnet_group_name=f'aurora-mysql-{self.stack_name}',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    #XXX: Supported Regions and DB engines for Amazon RDS zero-ETL integrations with Amazon Redshift
    # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RDS_Fea_Regions_DB-eng.Feature.ZeroETL.html
    #XXX: MySQL on Amazon RDS versions
    # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/MySQL.Concepts.VersionMgmt.html
    rds_engine = aws_rds.DatabaseInstanceEngine.mysql(version=aws_rds.MysqlEngineVersion.VER_8_0_40)

    #XXX: (Amazon RDS User Guide) Parameters for MySQL
    # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.MySQL.Parameters.html
    rds_param_group = aws_rds.ParameterGroup(self, 'MySQLDBParamGroup',
      engine=rds_engine,
      description='Custom parameter group for mysql8.x',
      name=f"{db_instance_name}-pg",
      parameters={
        'slow_query_log': '1',
        'wait_timeout': '300',
        'character-set-client-handshake': '0',
        'character_set_server': 'utf8mb4',
        'collation_server': 'utf8mb4_unicode_ci',
        'init_connect': 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci',
        # 'binlog_format': 'ROW', #XXX: Turn on binlog
      },
      removal_policy=cdk.RemovalPolicy.DESTROY
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

    rds_instance_engine = aws_rds.DatabaseInstanceEngine.MYSQL
    primary_instance = aws_rds.DatabaseInstance(self, "MySQLDBPrimary",
      engine=rds_instance_engine,
      credentials=rds_credentials,
      instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.R6G, aws_ec2.InstanceSize.XLARGE2),
      vpc=vpc,
      auto_minor_version_upgrade=False,
      backup_retention=cdk.Duration.days(3),
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      enable_performance_insights=True,
      instance_identifier=db_instance_name,
      # multi_az=False,
      parameter_group=rds_param_group,
      #XXX: The backup window and maintenance window must not overlap.
      preferred_backup_window='17:00-18:00', # hh24:mi-hh24:mi
      preferred_maintenance_window='Sun:18:00-Sun:19:00', # ddd:hh24:mi-ddd:hh24:mi
      removal_policy=cdk.RemovalPolicy.SNAPSHOT,
      security_groups=[sg_mysql_server],
      subnet_group=rds_subnet_group
    )

    replica_instance = aws_rds.DatabaseInstanceReadReplica(self, "MySQLDBReadReplica",
      source_database_instance=primary_instance,
      instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.R6G, aws_ec2.InstanceSize.XLARGE2),
      vpc=vpc,
      auto_minor_version_upgrade=False,
      backup_retention=cdk.Duration.days(3),
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      enable_performance_insights=True,
      instance_identifier=f"{db_instance_name}-readreplica",
      # multi_az=False,
      parameter_group=rds_param_group,
      #XXX: The backup window and maintenance window must not overlap.
      preferred_backup_window='16:30-17:30', # hh24:mi-hh24:mi
      preferred_maintenance_window='Sun:17:30-Sun:18:30', #ddd:hh24:mi-ddd:hh24:mi
      removal_policy=cdk.RemovalPolicy.SNAPSHOT,
      security_groups=[sg_mysql_server],
      subnet_group=rds_subnet_group
    )


    cdk.CfnOutput(self, 'DBPrimaryEndpoint',
      value=primary_instance.db_instance_endpoint_address,
      export_name=f'{self.stack_name}-DBPrimaryEndpoint')
    cdk.CfnOutput(self, 'DBReplicaEndpoint',
      value=replica_instance.db_instance_endpoint_address,
      export_name=f'{self.stack_name}-DBReplicaEndpoint')
    cdk.CfnOutput(self, 'DBInstanceEndpointPort',
      value=primary_instance.db_instance_endpoint_port,
      export_name=f'{self.stack_name}-DBInstanceEndpointPort')
    cdk.CfnOutput(self, 'RDSClientSecurityGroupId',
      value=self.sg_mysql_client.security_group_id,
      export_name=f'{self.stack_name}-RDSClientSecurityGroupId')
    cdk.CfnOutput(self, 'DBSecretName',
      value=primary_instance.secret.secret_name,
      export_name=f'{self.stack_name}-DBSecretName')
