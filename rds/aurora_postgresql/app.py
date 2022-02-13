#!/usr/bin/env python3
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

class AuroraPostgresqlStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    vpc_name = self.node.try_get_context("vpc_name")
    vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
      is_default=True,
      vpc_name=vpc_name)

    sg_use_mysql = aws_ec2.SecurityGroup(self, 'PostgreSQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql client',
      security_group_name='default-postgresql-client-sg'
    )
    cdk.Tags.of(sg_use_mysql).add('Name', 'default-postgresql-client-sg')

    sg_mysql_server = aws_ec2.SecurityGroup(self, 'PostgreSQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql',
      security_group_name='default-postgresql-server-sg'
    )
    sg_mysql_server.add_ingress_rule(peer=sg_use_mysql, connection=aws_ec2.Port.tcp(5432),
      description='default-postgresql-client-sg')
    sg_mysql_server.add_ingress_rule(peer=sg_mysql_server, connection=aws_ec2.Port.all_tcp(),
      description='default-postgresql-server-sg')
    cdk.Tags.of(sg_mysql_server).add('Name', 'default-postgresql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'PostgreSQLSubnetGroup',
      description='subnet group for postgresql',
      subnet_group_name='aurora-postgresql',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_NAT),
      vpc=vpc
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

    rds_engine = aws_rds.DatabaseClusterEngine.aurora_postgres(version=aws_rds.AuroraPostgresEngineVersion.VER_13_4)

    #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.ParameterGroups.html#AuroraPostgreSQL.Reference.Parameters.Cluster
    rds_cluster_param_group = aws_rds.ParameterGroup(self, 'AuroraPostgreSQLClusterParamGroup',
      engine=rds_engine,
      description='Custom cluster parameter group for aurora-postgresql13',
      parameters={
        'log_min_duration_statement': '15000', # 15 sec
        'default_transaction_isolation': 'read committed',
        'client_encoding': 'UTF8'
      }
    )

    #XXX: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Reference.ParameterGroups.html#AuroraPostgreSQL.Reference.Parameters.Instance
    rds_db_param_group = aws_rds.ParameterGroup(self, 'AuroraPostgreSQLDBParamGroup',
      engine=rds_engine,
      description='Custom parameter group for aurora-postgresql13',
      parameters={
        'log_min_duration_statement': '15000', # 15 sec
        'default_transaction_isolation': 'read committed'
      }
    )

    db_cluster = aws_rds.DatabaseCluster(self, 'Database',
      engine=rds_engine,
      credentials=rds_credentials,
      instance_props={
        'instance_type': aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
        'parameter_group': rds_db_param_group,
        'vpc_subnets': {
          'subnet_type': aws_ec2.SubnetType.PRIVATE_WITH_NAT
        },
        'vpc': vpc,
        'auto_minor_version_upgrade': False,
        'security_groups': [sg_mysql_server]
      },
      instances=2,
      parameter_group=rds_cluster_param_group,
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      cluster_identifier=db_cluster_name,
      subnet_group=rds_subnet_group,
      backup=aws_rds.BackupProps(
        retention=cdk.Duration.days(3),
        preferred_window="03:00-04:00"
      )
    )

    cdk.CfnOutput(self, 'DBClusterEndpoint', value=db_cluster.cluster_endpoint.socket_address, export_name='DBClusterEndpoint')
    cdk.CfnOutput(self, 'DBClusterReadEndpoint', value=db_cluster.cluster_read_endpoint.socket_address, export_name='DBClusterReadEndpoint')


app = cdk.App()
AuroraPostgresqlStack(app, "AuroraPostgreSQLStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
