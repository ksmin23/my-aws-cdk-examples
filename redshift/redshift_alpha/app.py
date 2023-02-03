#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_redshift_alpha
)
from constructs import Construct


class RedshiftStack(Stack):

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
    # vpc = aws_ec2.Vpc.from_lookup(self, "RedshiftVPC",
    #   is_default=True,
    #   vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    vpc = aws_ec2.Vpc(self, "RedshiftVPC",
      max_azs=2,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        )
      }
    )

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

    redshift_cluster = aws_redshift_alpha.Cluster(self, "Redshift",
      master_user=aws_redshift_alpha.Login(
        master_username="admin"
      ),
      vpc=vpc,
      enhanced_vpc_routing=True,
      node_type=aws_redshift_alpha.NodeType.RA3_XLPLUS,
      preferred_maintenance_window="Sun:03:00-Sun:04:00",
      security_groups=[sg_rs_cluster],
      # removal_policy=cdk.RemovalPolicy.DESTROY
    )
    redshift_cluster.add_to_parameter_group("enable_user_activity_logging", "true")

    cdk.CfnOutput(self, f'{self.stack_name}-ClusterEndpoint',
      value=f'{redshift_cluster.cluster_endpoint.hostname}:{redshift_cluster.cluster_endpoint.port}')
    cdk.CfnOutput(self, f'{self.stack_name}-SecretArn',
      value=f'{redshift_cluster.secret.secret_arn}')


app = cdk.App()
RedshiftStack(app, "RedshiftClusterProvisioned",
  env=cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
