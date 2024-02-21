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


class AuroraPostgresqlServerlessV2Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    db_cluster_name = self.node.try_get_context('db_cluster_name')

    sg_postgresql_client = aws_ec2.SecurityGroup(self, 'PostgreSQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql client',
      security_group_name=f'{db_cluster_name}-postgresql-client-sg'
    )
    cdk.Tags.of(sg_postgresql_client).add('Name', 'postgresql-client-sg')

    sg_postgresql_server = aws_ec2.SecurityGroup(self, 'PostgreSQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql',
      security_group_name=f'{db_cluster_name}-postgresql-server-sg'
    )
    sg_postgresql_server.add_ingress_rule(peer=sg_postgresql_client, connection=aws_ec2.Port.tcp(5432),
      description='postgresql-client-sg')
    sg_postgresql_server.add_ingress_rule(peer=sg_postgresql_server, connection=aws_ec2.Port.all_tcp(),
      description='postgresql-server-sg')
    cdk.Tags.of(sg_postgresql_server).add('Name', 'postgresql-server-sg')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'PostgreSQLSubnetGroup',
      description='subnet group for postgresql',
      subnet_group_name=f'aurora-postgresql-{self.stack_name.lower()}',
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      vpc=vpc
    )

    rds_engine = aws_rds.DatabaseClusterEngine.AURORA_POSTGRESQL
    rds_param_group = aws_rds.ParameterGroup.from_parameter_group_name(
      self,
      'AuroraPostgreSQLParamGroup',
      'default.aurora-postgresql15'
    )

    #XXX: In order to exclude punctuations when generating a password
    # use aws_secretsmanager.Secret instead of aws_rds.DatabaseSecret.
    # Othwerise, an error occurred such as:
    # "All characters of the desired type have been excluded"
    db_secret = aws_secretsmanager.Secret(self, "DatabaseSecret",
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "postgres"}),
        generate_string_key="password",
        exclude_punctuation=True,
        password_length=8
      )
    )
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    #XXX: [GitHub Issues] aws_rds: Add support for the Data API to DatabaseCluster construct (created at 2024-01-04)
    # https://github.com/aws/aws-cdk/issues/28574
    db_cluster = aws_rds.DatabaseCluster(self, 'AuroraPostgresDBCluster',
      engine=rds_engine,
      credentials=rds_credentials, # A username of 'admin' (or 'postgres' for PostgreSQL) and SecretsManager-generated password
      writer=aws_rds.ClusterInstance.serverless_v2("writer",
        parameter_group=rds_param_group,
        auto_minor_version_upgrade=False
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
          parameter_group=rds_param_group,
          auto_minor_version_upgrade=False
        )
      ],
      parameter_group=rds_param_group,
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      cluster_identifier=db_cluster_name,
      subnet_group=rds_subnet_group,
      backup=aws_rds.BackupProps(
        retention=cdk.Duration.days(3),
        preferred_window="03:00-04:00"
      ),
      security_groups=[sg_postgresql_server],
      vpc=vpc,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS)
    )

    #XXX: Enable RDS Data API via "layer 1" shenanigans
    # https://github.com/aws/aws-cdk/issues/28574#issuecomment-1934085237
    # https://stackoverflow.com/questions/54931548/enable-aurora-data-api-from-cloudformation
    db_cluster.node.default_child.add_override('Properties.EnableHttpEndpoint', True);


    cdk.CfnOutput(self, 'RDSClientSecurityGroupId', value=sg_postgresql_client.security_group_id,
                  export_name=f'{self.stack_name}-RDSClientSecurityGroupId')
    cdk.CfnOutput(self, 'DBSecretName', value=db_cluster.secret.secret_name,
                  export_name=f'{self.stack_name}-DBSecretName')
    cdk.CfnOutput(self, 'DBClusterEndpoint', value=db_cluster.cluster_endpoint.socket_address,
                  export_name=f'{self.stack_name}-DBClusterEndpoint')
