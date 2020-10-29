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
    core.Tags.of(sg_mysql_server).add('Name', 'mysql-server')

    sg_mysql_server.add_ingress_rule(peer=sg_use_mysql, connection=aws_ec2.Port.tcp(3306),
      description='use-default-mysql')

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
    db_secret_name = '{kind}/{dbCluster}/{rdsType}'.format(kind='prod',
      dbCluster=db_cluster_name, rdsType='AuroraMySQL')
    aws_secretsmanager.Secret(self, 'TemplatedDBSecret',
      description='automatically generated database secret',
      secret_name=db_secret_name,
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "admin"}),
        generate_string_key='password',
        exclude_characters=''' "%+~`#$&*()|[]{}:;<>?!'/''',
        exclude_punctuation=True
      ),
      removal_policy=core.RemovalPolicy.RETAIN
    )
    db_secret = aws_secretsmanager.Secret.from_secret_name(self, 'DBSecret', db_secret_name)
    rds_credentials = aws_rds.Credentials.from_secret(db_secret)

    cluster = aws_rds.DatabaseCluster(self, 'Database',
      engine=rds_engine,
      credentials=rds_credentials,
      instance_props={
        'instance_type': aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM),
        'parameter_group': rds_db_param_group,
        'vpc_subnets': {
          'subnet_type': aws_ec2.SubnetType.PUBLIC
        },
        'vpc': vpc,
        'auto_minor_version_upgrade': False,
        'security_groups': [sg_mysql_server]
      },
      instances=2,
      parameter_group=rds_cluster_param_group,
      cloudwatch_logs_retention=aws_logs.RetentionDays.THREE_DAYS,
      cluster_identifier=db_cluster_name,
      subnet_group=rds_subnet_group
    )


app = core.App()
AuroraMysqlStack(app, "aurora-mysql", env=core.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]))

app.synth()
