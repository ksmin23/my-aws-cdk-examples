#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_redshiftserverless,
  aws_secretsmanager
)
from constructs import Construct


class RedshiftServerlessStack(Stack):

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
    # vpc = aws_ec2.Vpc.from_lookup(self, "RedshiftServerlessVPC",
    #   is_default=True,
    #   vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    vpc = aws_ec2.Vpc(self, "RedshiftServerlessVPC",
      max_azs=2,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

    secret_name = self.node.try_get_context('aws_secret_name')
    rs_admin_user_secret = aws_secretsmanager.Secret.from_secret_name_v2(self,
      'RedshiftAdminUserSecret',
      secret_name)

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

    cfn_rss_namespace = aws_redshiftserverless.CfnNamespace(self, 'RedshiftServerlessCfnNamespace',
      namespace_name=REDSHIFT_NAMESPACE_NAME,

      # the properties below are optional
      admin_username=rs_admin_user_secret.secret_value_from_json("admin_username").unsafe_unwrap(),
      admin_user_password=rs_admin_user_secret.secret_value_from_json("admin_user_password").unsafe_unwrap(),
      db_name=REDSHIFT_DB_NAME,
      log_exports=['userlog', 'connectionlog', 'useractivitylog']
    )

    cfn_rss_workgroup = aws_redshiftserverless.CfnWorkgroup(self, 'RedshiftServerlessCfnWorkgroup',
      workgroup_name=REDSHIFT_WORKGROUP_NAME,

      # the properties below are optional
      base_capacity=128,
      enhanced_vpc_routing=True,
      namespace_name=cfn_rss_namespace.namespace_name,
      publicly_accessible=False,
      security_group_ids=[sg_rs_cluster.security_group_id],
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids
    )
    cfn_rss_workgroup.add_dependency(cfn_rss_namespace)
    cfn_rss_workgroup.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
 
    cdk.CfnOutput(self, f'{self.stack_name}-NamespaceName',
      value=cfn_rss_workgroup.namespace_name, export_name=f'{self.stack_name}-NamespaceName')
    cdk.CfnOutput(self, f'{self.stack_name}-WorkgroupName',
      value=cfn_rss_workgroup.workgroup_name, export_name=f'{self.stack_name}-WorkgroupName')


app = cdk.App()
RedshiftServerlessStack(app, "RedshiftServerlessStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
