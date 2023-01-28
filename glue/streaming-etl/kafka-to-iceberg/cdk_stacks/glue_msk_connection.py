#!/usr/bin/env python3
import boto3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_glue,
  aws_msk
)
from constructs import Construct


class GlueMSKConnectionStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, sg_msk_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_glue_cluster = aws_ec2.SecurityGroup(self, 'GlueClusterSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon Glue Cluster',
      security_group_name='glue-cluster-sg'
    )
    sg_glue_cluster.add_ingress_rule(peer=sg_glue_cluster, connection=aws_ec2.Port.all_tcp(),
      description='inter-communication between glue cluster nodes')
    cdk.Tags.of(sg_glue_cluster).add('Name', 'glue-cluster-sg')

    msk_cluster_name = self.node.try_get_context('msk').get('cluster_name')
    msk_client = boto3.client('kafka', region_name=vpc.env.region)
    response = msk_client.list_clusters(ClusterNameFilter=msk_cluster_name)
    msk_cluster_info_list = response['ClusterInfoList']
    if not msk_cluster_info_list:
      kafka_bootstrap_servers = "localhost:9094"
    else:
      msk_cluster_arn = msk_cluster_info_list[0]['ClusterArn']
      msk_brokers = msk_client.get_bootstrap_brokers(ClusterArn=msk_cluster_arn)
      kafka_bootstrap_servers = msk_brokers['BootstrapBrokerString']
      assert kafka_bootstrap_servers

    connection_properties = {
      "KAFKA_BOOTSTRAP_SERVERS": kafka_bootstrap_servers,
      "KAFKA_SSL_ENABLED": "false"
    }
  
    subnet = vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets[0]

    connection_input_property = aws_glue.CfnConnection.ConnectionInputProperty(
      connection_type="KAFKA",
      connection_properties=connection_properties,
      name="msk-connector",
      physical_connection_requirements=aws_glue.CfnConnection.PhysicalConnectionRequirementsProperty(
        security_group_id_list=[sg_msk_client.security_group_id, sg_glue_cluster.security_group_id],
        subnet_id=subnet.subnet_id,
        availability_zone=subnet.availability_zone
      )
    )

    msk_connection = aws_glue.CfnConnection(self, 'GlueMSKConnector',
      catalog_id=cdk.Aws.ACCOUNT_ID,
      connection_input=connection_input_property
    )

    self.msk_connection_info = msk_connection.connection_input

    cdk.CfnOutput(self, f'{self.stack_name}-MSKConnectorName', value=self.msk_connection_info.name)
