#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
import json

from aws_cdk import (
  core,
  aws_ec2,
  aws_iam,
  aws_logs,
  aws_rds,
  aws_secretsmanager
)


class AuroraMysqlStack(core.Stack):

  def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    # The code that defines your stack goes here
    vpc_name = self.node.try_get_context("vpc_name")
    vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
      is_default=True,
      vpc_name=vpc_name)

    sg_use_mysql = aws_ec2.SecurityGroup(self, 'MySQLClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql client',
      security_group_name='use-default-mysql'
    )
    core.Tags.of(sg_use_mysql).add('Name', 'use-default-mysql')

    sg_mysql_server = aws_ec2.SecurityGroup(self, 'MySQLServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql',
      security_group_name='default-mysql-server'
    )
    sg_mysql_server.add_ingress_rule(peer=sg_use_mysql, connection=aws_ec2.Port.tcp(3306),
      description='use-default-mysql')
    core.Tags.of(sg_mysql_server).add('Name', 'mysql-server')

    rds_subnet_group = aws_rds.SubnetGroup(self, 'RdsSubnetGroup',
      description='subnet group for mysql',
      subnet_group_name='aurora-mysql', # Optional - name will be generated
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE),
      vpc=vpc
    )

    rds_engine = aws_rds.DatabaseClusterEngine.aurora_mysql(version=aws_rds.AuroraMysqlEngineVersion.VER_2_08_1)

    rds_cluster_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLClusterParamGroup',
      engine=rds_engine,
      description='Custom cluster parameter group for aurora-mysql5.7',
      parameters={
        'tx_isolation': 'READ-COMMITTED',
        'wait_timeout': '300',
        'init_connect': 'SET collation_connection=utf8mb4_unicode_ci',
        'collation_server': 'utf8mb4_unicode_ci',
        'character_set_server': 'utf8mb4'
      }
    )

    rds_db_param_group = aws_rds.ParameterGroup(self, 'AuroraMySQLDBParamGroup',
      engine=rds_engine,
      description='Custom parameter group for aurora-mysql5.7',
      parameters={
        'tx_isolation': 'READ-COMMITTED',
        'wait_timeout': '300',
        'init_connect': 'SET collation_connection=utf8mb4_unicode_ci'
      }
    )

    db_cluster_name = self.node.try_get_context('db_cluster_name')
    #XXX: aws_rds.Credentials.from_username(username, ...) can not be given user specific Secret name
    #XXX: therefore, first create Secret and then use it to create database
    db_secret_name = self.node.try_get_context('db_secret_name')
    db_secret_arn = self.format_arn(region=core.Aws.REGION, resource='secret',
      service='secretsmanager', resource_name=db_secret_name)
    db_secret = aws_secretsmanager.Secret.from_secret_arn(self, 'DBSecretFromArn', db_secret_arn)
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    db_cluster = aws_rds.DatabaseCluster(self, 'Database',
      engine=rds_engine,
      credentials=rds_credentials,
      instance_props={
        'instance_type': aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
        'parameter_group': rds_db_param_group,
        'vpc_subnets': {
          'subnet_type': aws_ec2.SubnetType.PRIVATE
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
        retention=core.Duration.days(3),
        preferred_window="03:00-04:00"
      )
    )
    
    sg_mysql_public_proxy = aws_ec2.SecurityGroup(self, 'MySQLPublicProxySG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for mysql public proxy',
      security_group_name='default-mysql-public-proxy'
    )
    sg_mysql_public_proxy.add_ingress_rule(peer=aws_ec2.Peer.any_ipv4(), connection=aws_ec2.Port.tcp(3306), description='mysql public proxy')
    core.Tags.of(sg_mysql_public_proxy).add('Name', 'mysql-public-proxy')

    #XXX: Datbase Proxy use only Secret Arn of target database or database cluster
    #XXX: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-rds-dbproxy-authformat.html
    db_proxy = aws_rds.DatabaseProxy(self, 'DBProxy',
      proxy_target=aws_rds.ProxyTarget.from_cluster(db_cluster),
      secrets=[db_secret],
      vpc=vpc,
      db_proxy_name='{}-proxy'.format(db_cluster_name),
      idle_client_timeout=core.Duration.minutes(10),
      max_connections_percent=90,
      max_idle_connections_percent=10,
      security_groups=[sg_use_mysql, sg_mysql_public_proxy],
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )


app = core.App()
AuroraMysqlStack(app, "aurora-mysql", env=core.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
