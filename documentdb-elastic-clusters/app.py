#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_docdbelastic,
  aws_ec2,
)
from constructs import Construct

class DocumentDbElasticClustersStack(Stack):
  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    vpc_name = self.node.try_get_context("vpc_name")
    vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
      is_default=True,
      vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    # vpc = aws_ec2.Vpc(self, "WebAnalyticsVPC",
    #   max_azs=2,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    sg_docdb_client = aws_ec2.SecurityGroup(self, 'DocDBClientSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for documentdb elastic clusters client',
      security_group_name='docdbelastic-client-sg'
    )
    cdk.Tags.of(sg_docdb_client).add('Name', 'docdbelastic-client-sg')

    sg_docdb_server = aws_ec2.SecurityGroup(self, 'DocDBServerSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for documentdb elastic clusters',
      security_group_name='docdbelastic-cluster-sg'.format(stack_name=self.stack_name)
    )
    sg_docdb_server.add_ingress_rule(peer=sg_docdb_client, connection=aws_ec2.Port.tcp(27017),
      description='docdbelastic-client-sg')
    cdk.Tags.of(sg_docdb_server).add('Name', 'docdbelastic-cluster-sg')

    docdb_cluster_name = self.node.try_get_context('docdb_cluster_name') or self.stack_name

    docdb_cluster = aws_docdbelastic.CfnCluster(self, 'DocDBElasticCluster',
      admin_user_name='docdbadmin',
      auth_type='PLAIN_TEXT', # [PLAIN_TEXT, SECRET_ARN]
      cluster_name=docdb_cluster_name,
      shard_capacity=8, # Allowed values: [2, 4, 8, 16, 32, 64]
      shard_count=4, # The maximum number of shards per cluster: 32

      # the properties below are optional
      #admin_user_password='adminUserPassword',
      preferred_maintenance_window='sun:18:00-sun:18:30',
      subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      vpc_security_group_ids=[sg_docdb_server.security_group_id]
    )
    docdb_cluster.apply_removal_policy(cdk.RemovalPolicy.RETAIN)

    cdk.CfnOutput(self, f'{self.stack_name}-DocDbElasticClusterArn', value=docdb_cluster.attr_cluster_arn,
        export_name=f'{self.stack_name}-DocDbElasticClusterArn')


app = cdk.App()
DocumentDbElasticClustersStack(app, "DocDbElasticStack",
  env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()

