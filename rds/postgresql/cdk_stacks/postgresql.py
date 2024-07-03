#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_rds,
)
from constructs import Construct


class PostgresqlDBStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    db_cluster_name = self.node.try_get_context('db_cluster_name')

    sg_postgresql_client = aws_ec2.SecurityGroup(self, 'PostgresqlDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql client',
      security_group_name=f'postgresql-client-sg-{db_cluster_name}'
    )
    cdk.Tags.of(sg_postgresql_client).add('Name', 'postgresql-client-sg')

    sg_postgresql_server = aws_ec2.SecurityGroup(self, 'PostgresqlDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for postgresql',
      security_group_name=f'postgresql-server-sg-{db_cluster_name}'
    )
    sg_postgresql_server.add_ingress_rule(peer=sg_postgresql_client, connection=aws_ec2.Port.tcp(5432),
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
    db_cluster_param_group = aws_rds.CfnDBClusterParameterGroup(self, "PostgresqlClusterParamGroup",
      family='postgres16',
      parameters={
        'log_min_duration_statement': '15000', # 15 sec
        'default_transaction_isolation': 'read committed',
        'client_encoding': 'UTF8',
        'rds.allowed_extensions': '*',
        'shared_preload_libraries': 'pg_stat_statements'
      },
      description='Custom db cluster parameter group for postgres16',
      db_cluster_parameter_group_name=f'db-cluster-param-group-{db_cluster_name.lower()}'
    )

    #XXX: To list all of the available parameter group families, use the following command:
    # aws rds describe-db-engine-versions --query "DBEngineVersions[].DBParameterGroupFamily"
    db_instance_param_group = aws_rds.CfnDBParameterGroup(self, "PostgresqlDBParamGroup",
      family='postgres16',
      parameters={
        'log_min_duration_statement': '15000', # 15 sec
        'default_transaction_isolation': 'read committed',
        'rds.allowed_extensions': '*',
        'shared_preload_libraries': 'pg_stat_statements'
      },
      description='Custom db instance parameter group for postgres16',
      db_parameter_group_name=f'db-instance-param-group-{db_cluster_name.lower()}'
    )

    db_cluster = aws_rds.CfnDBCluster(self, "PostgresqlDBCluster",
      allocated_storage=100,
      auto_minor_version_upgrade=False,
      backup_retention_period=3, # days
      db_cluster_identifier=db_cluster_name,
      #XXX: To determine the DB instance classes supported by each DB engine in a specific AWS Region,
      # see the following link:
      # https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.html#Concepts.DBInstanceClass.Support
      db_cluster_instance_class="db.r6gd.large",
      #XXX: aws_rds.CfnDBClusterParameterGroup.db_cluster_parameter_group_name is None
      # So use aws_rds.CfnDBClusterParameterGroup.ref
      db_cluster_parameter_group_name=db_cluster_param_group.ref,
      db_instance_parameter_group_name=db_instance_param_group.attr_db_parameter_group_name,
      db_subnet_group_name=rds_subnet_group.subnet_group_name,
      engine="postgres",
      engine_mode="provisioned",
      engine_version=aws_rds.PostgresEngineVersion.VER_16_3.postgres_full_version,
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
    db_cluster.add_dependency(db_cluster_param_group)
    db_cluster.add_dependency(db_instance_param_group)


    cdk.CfnOutput(self, 'DBClusterEndpoint',
      value=f"{db_cluster.attr_endpoint_address}:{db_cluster.attr_endpoint_port}",
      export_name=f'{self.stack_name}-DBClusterEndpoint')
    cdk.CfnOutput(self, 'DBClusterReadEndpoint',
      value=f"{db_cluster.attr_read_endpoint_address}:{db_cluster.attr_endpoint_port}",
      export_name=f'{self.stack_name}-DBClusterReadEndpoint')
    cdk.CfnOutput(self, 'DBClusterParamGroupName',
      value=db_cluster_param_group.ref,
      export_name=f'{self.stack_name}-DBClusterParamGroupName')
    cdk.CfnOutput(self, 'DBInstanceParamGroupName',
      value=db_instance_param_group.attr_db_parameter_group_name,
      export_name=f'{self.stack_name}-DBInstanceParamGroupName')
