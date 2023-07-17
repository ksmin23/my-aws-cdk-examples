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

class PostgresqlDBStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context("vpc_name") or "default"
    # vpc = aws_ec2.Vpc.from_lookup(self, "PostgresqlVPC",
    #   is_default=True,
    #   vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    vpc = aws_ec2.Vpc(self, "PostgresqlDBVPC",
      max_azs=3,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    sg_use_postgresql = aws_ec2.SecurityGroup(self, 'PostgresqlDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql client',
      security_group_name='postgresql-client-sg'
    )
    cdk.Tags.of(sg_use_postgresql).add('Name', 'postgresql-client-sg')

    sg_postgresql_server = aws_ec2.SecurityGroup(self, 'PostgresqlDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql',
      security_group_name='postgresql-server-sg'
    )
    sg_postgresql_server.add_ingress_rule(peer=sg_use_postgresql, connection=aws_ec2.Port.tcp(5432),
      description='postgresql-client-sg')
    sg_postgresql_server.add_ingress_rule(peer=sg_postgresql_server, connection=aws_ec2.Port.all_tcp(),
      description='postgresql-server-sg')
    cdk.Tags.of(sg_postgresql_server).add('Name', 'postgresql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'PostgresqlDBSubnetGroup',
      description='subnet group for postgresql',
      subnet_group_name='rds-postgresql',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    #XXX: To list all of the available parameter group families, use the following command:
    # aws rds describe-db-engine-versions --query "DBEngineVersions[].DBParameterGroupFamily"
    rds_cluster_param_group = aws_rds.CfnDBClusterParameterGroup(self, "PostgresqlClusterParamGroup",
      family="postgres15",
      parameters={
        'log_min_duration_statement': '15000', # 15 sec
        'default_transaction_isolation': 'read committed',
        'client_encoding': 'UTF8',
        'rds.allowed_extensions': '*',
        'shared_preload_libraries': 'pg_stat_statements'
      },
      description=f'Custom cluster parameter group for {aws_rds.PostgresEngineVersion.postgres_major_version}'
    )

    #XXX: To list all of the available parameter group families, use the following command:
    # aws rds describe-db-engine-versions --query "DBEngineVersions[].DBParameterGroupFamily"
    rds_db_param_group = aws_rds.CfnDBParameterGroup(self, "PostgresqlDBParamGroup",
      family="postgres15",
      parameters={
        'log_min_duration_statement': '15000', # 15 sec
        'default_transaction_isolation': 'read committed',
        'rds.allowed_extensions': '*',
        'shared_preload_libraries': 'pg_stat_statements'
      },
      description=f'Custom parameter group for {aws_rds.PostgresEngineVersion.postgres_major_version}',
    )

    db_cluster_name = self.node.try_get_context('db_cluster_name')

    #XXX: aws_rds.Credentials.from_username(username, ...) can not be given user specific Secret name
    # therefore, first create Secret and then use it to create database
    db_secret_name = self.node.try_get_context('db_secret_name')
    #XXX: arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
    db_secret_arn = 'arn:aws:secretsmanager:{region}:{account}:secret:{resource_name}'.format(
      region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID, resource_name=db_secret_name)
    db_secret = aws_secretsmanager.Secret.from_secret_partial_arn(self, 'DBSecretFromArn', db_secret_arn)

    db_cluster = aws_rds.CfnDBCluster(self, "PostgresqlDBCluster",
      allocated_storage=100,
      auto_minor_version_upgrade=False,
      backup_retention_period=3, # days
      db_cluster_identifier=db_cluster_name,
      #XXX: To determine the DB instance classes supported by each DB engine in a specific AWS Region,
      # see the following link:
      # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html#Concepts.DBInstanceClass.Support
      db_cluster_instance_class="db.r6gd.large",
      db_cluster_parameter_group_name=rds_cluster_param_group.db_cluster_parameter_group_name,
      db_instance_parameter_group_name=rds_db_param_group.db_parameter_group_name,
      db_subnet_group_name=rds_subnet_group.subnet_group_name,
      engine="postgres",
      engine_mode="provisioned",
      engine_version=aws_rds.PostgresEngineVersion.VER_15_3.postgres_full_version, # "15.3",
      manage_master_user_password=True,
      master_username="postgres",
      port=5432,
      preferred_backup_window="03:00-04:00",
      preferred_maintenance_window="Sun:04:30-Sun:05:30",
      publicly_accessible=False,
      #XXX: For information about valid IOPS values, see Provisioned IOPS storage in the Amazon RDS User Guide
      # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Storage.html#USER_PIOPS
      iops=3000,
      storage_type="io1",
      vpc_security_group_ids=[sg_postgresql_server.security_group_id]
    )


    cdk.CfnOutput(self, 'DBClusterEndpoint',
      value=f"{db_cluster.attr_endpoint_address}:{db_cluster.attr_endpoint_port}",
      export_name='PgsqlDBClusterEndpoint')
    cdk.CfnOutput(self, 'DBClusterReadEndpoint',
      value=f"{db_cluster.attr_read_endpoint_address}:{db_cluster.attr_endpoint_port}",
      export_name='PgsqlDBClusterReadEndpoint')
    cdk.CfnOutput(self, 'DBSecret', value=db_secret.secret_name, export_name='PgsqlDBSecret')


app = cdk.App()
PostgresqlDBStack(app, "PostgresqlDBStack", env=cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
