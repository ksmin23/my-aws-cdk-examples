#!/usr/bin/env python3

import json
import boto3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_redshiftserverless
)
from constructs import Construct


class RedshiftServerlessStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sm_client = boto3.client('secretsmanager', region_name=kwargs['env'].region)
    secret_name = self.node.try_get_context('aws_secret_name')
    secret_value = sm_client.get_secret_value(SecretId=secret_name)
    redshift_secret = json.loads(secret_value['SecretString'])

    REDSHIFT_DB_NAME = self.node.try_get_context('db_name') or 'dev'
    REDSHIFT_NAMESPACE_NAME = self.node.try_get_context('namespace') or 'rss-demo-ns'
    REDSHIFT_WORKGROUP_NAME = self.node.try_get_context('workgroup') or 'rss-demo-wg'

    sg_rs_client = aws_ec2.SecurityGroup(self, 'RedshiftClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redshift client',
      security_group_name='redshift-client-sg'
    )
    cdk.Tags.of(sg_rs_client).add('Name', 'redshift-client-sg')

    sg_rs_cluster = aws_ec2.SecurityGroup(self, 'RedshiftClusterSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for redshift cluster nodes',
      security_group_name='redshift-cluster-sg'
    )
    sg_rs_cluster.add_ingress_rule(peer=sg_rs_client, connection=aws_ec2.Port.tcp(5439),
      description='redshift-client-sg')
    sg_rs_cluster.add_ingress_rule(peer=sg_rs_cluster, connection=aws_ec2.Port.all_tcp(),
      description='redshift-cluster-sg')
    cdk.Tags.of(sg_rs_cluster).add('Name', 'redshift-cluster-sg')

    redshift_streaming_role = aws_iam.Role(self, "RedshiftStreamingRole",
      role_name='RedshiftStreamingRole',
      assumed_by=aws_iam.ServicePrincipal('redshift.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonKinesisReadOnlyAccess'),
      ]
    )

    cfn_rss_namespace = aws_redshiftserverless.CfnNamespace(self, 'RedshiftServerlessCfnNamespace',
      namespace_name=REDSHIFT_NAMESPACE_NAME,
      admin_username=redshift_secret['admin_username'],
      admin_user_password=redshift_secret['admin_user_password'],
      db_name=REDSHIFT_DB_NAME,
      iam_roles=[redshift_streaming_role.role_arn],
      log_exports=['userlog', 'connectionlog', 'useractivitylog']
    )

    cfn_rss_workgroup = aws_redshiftserverless.CfnWorkgroup(self, 'RedshiftServerlessCfnWorkgroup',
      workgroup_name=REDSHIFT_WORKGROUP_NAME,
      base_capacity=128,
      enhanced_vpc_routing=True,
      namespace_name=cfn_rss_namespace.namespace_name,
      publicly_accessible=False,
      security_group_ids=[sg_rs_cluster.security_group_id],
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
    )
    cfn_rss_workgroup.add_depends_on(cfn_rss_namespace)
    cfn_rss_workgroup.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
 
    cdk.CfnOutput(self, f'{self.stack_name}-NamespaceName',
      value=cfn_rss_workgroup.namespace_name, export_name=f'{self.stack_name}-NamespaceName')
    cdk.CfnOutput(self, f'{self.stack_name}-WorkgroupName',
      value=cfn_rss_workgroup.workgroup_name, export_name=f'{self.stack_name}-WorkgroupName')

