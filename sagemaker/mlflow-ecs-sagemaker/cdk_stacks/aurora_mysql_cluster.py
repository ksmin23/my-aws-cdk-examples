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


class AuroraMysqlClusterStack(Stack):

  def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    sg_mysql_client = aws_ec2.SecurityGroup(self, 'MySQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql client',
      security_group_name='aurora_mysql-client-sg'
    )
    cdk.Tags.of(sg_mysql_client).add('Name', 'aurora_mysql-client-sg')

    sg_mysql_server = aws_ec2.SecurityGroup(self, 'MySQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql',
      security_group_name='aurora_mysql-server-sg'
    )
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_client, connection=aws_ec2.Port.tcp(3306),
      description='aurora_mysql-client-sg')
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_server, connection=aws_ec2.Port.all_tcp(),
      description='aurora_mysql-server-sg')

    cdk.Tags.of(sg_mysql_server).add('Name', 'aurora_mysql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'MySQLSubnetGroup',
      description='subnet group for mysql',
      subnet_group_name=f'{self.stack_name}-aurora-mysql',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    #XXX: Aurora MySQL version numbers and special versions
    # https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.Versions.html
    rds_engine_version = aws_rds.AuroraMysqlEngineVersion.VER_3_04_0
    rds_engine = aws_rds.DatabaseClusterEngine.aurora_mysql(version=rds_engine_version)

    #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Reference.html#AuroraMySQL.Reference.Parameters.Cluster
    rds_cluster_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLClusterParamGroup',
      engine=rds_engine,
      description=f'Custom cluster parameter group for {rds_engine_version.aurora_mysql_major_version}',
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

    db_cluster_name = self.node.try_get_context('db_cluster_name') or 'mlflow'
    DB_NAME = "mlflowdb"

    #XXX: In order to exclude punctuations when generating a password
    # use aws_secretsmanager.Secret instead of aws_rds.DatabaseSecret.
    # Othwerise, an error occurred such as:
    # "All characters of the desired type have been excluded"
    db_secret = aws_secretsmanager.Secret(self, "DatabaseSecret",
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "admin"}),
        generate_string_key="password",
        exclude_punctuation=True,
        password_length=8
      )
    )
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    db_cluster = aws_rds.DatabaseCluster(self, 'Database',
      engine=rds_engine,
      credentials=rds_credentials, # A username of 'admin' (or 'postgres' for PostgreSQL) and SecretsManager-generated password
      default_database_name=DB_NAME,
      writer=aws_rds.ClusterInstance.provisioned("writer",
        instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
        parameter_group=rds_db_param_group,
        auto_minor_version_upgrade=False,
      ),
      #XXX: Choosing the Aurora Serverless v2 capacity range for an Aurora cluster
      # Keep in mind that if Global Database is in use or if Performance Insights is enabled,
      # the minimum is recommended to be 2 or above.
      # The maximum capacity for the instance may be set to the equivalent of the provisioned instance capacity
      # if it’s able to meet your workload requirements.
      # For example, if the CPU utilization for a db.r6g.4xlarge (128 GB) instance stays at 10% most times,
      # then the minimum ACUs may be set at 6.5 ACUs (10% of 128 GB) and maximum may be set at 64 ACUs (64x2GB=128GB).
      serverless_v2_min_capacity=2,
      serverless_v2_max_capacity=16,
      readers=[
        aws_rds.ClusterInstance.serverless_v2("reader1",
          scale_with_writer=True,
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

    self.sg_rds_client = sg_mysql_client
    self.database_name = DB_NAME
    self.database_secret = db_cluster.secret
    self.database_endpoint = db_cluster.cluster_endpoint

    cdk.CfnOutput(self, 'RDSClientSecurityGroupId', value=self.sg_rds_client.security_group_id,
                  export_name=f'{self.stack_name}-RDSClientSecurityGroupId')
    cdk.CfnOutput(self, 'DatabaseName', value=self.database_name,
                  export_name=f'{self.stack_name}-DatabaseName')
    cdk.CfnOutput(self, 'DBSecretName', value=self.database_secret.secret_name,
                  export_name=f'{self.stack_name}-DBSecretName')
    cdk.CfnOutput(self, 'DBClusterEndpoint', value=self.database_endpoint.socket_address,
                  export_name=f'{self.stack_name}-DBClusterEndpoint')
    cdk.CfnOutput(self, 'DBClusterReadEndpoint', value=db_cluster.cluster_read_endpoint.socket_address,
                  export_name=f'{self.stack_name}-DBClusterReadEndpoint')
