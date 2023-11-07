#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,

  aws_ec2,
  aws_logs,
  aws_msk_alpha as msk
)
from constructs import Construct


class MSKClusterStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    msk_cluster_name = self.node.try_get_context("msk_cluster_name")

    MSK_CLIENT_SG_NAME = f'msk-client-sg-{msk_cluster_name}'
    sg_msk_client = aws_ec2.SecurityGroup(self, 'KafkaClientSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK client',
      security_group_name=MSK_CLIENT_SG_NAME
    )
    cdk.Tags.of(sg_msk_client).add('Name', MSK_CLIENT_SG_NAME)

    MSK_CLUSTER_SG_NAME = f'msk-cluster-sg-{msk_cluster_name}'
    sg_msk_cluster = aws_ec2.SecurityGroup(self, 'MSKSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK Cluster',
      security_group_name=MSK_CLUSTER_SG_NAME
    )
    # For more information about the numbers of the ports that Amazon MSK uses to communicate with client machines,
    # see https://docs.aws.amazon.com/msk/latest/developerguide/port-info.html
    sg_msk_cluster.add_ingress_rule(peer=sg_msk_client, connection=aws_ec2.Port.tcp(2181),
      description='allow msk client to communicate with Apache ZooKeeper in plaintext')
    sg_msk_cluster.add_ingress_rule(peer=sg_msk_client, connection=aws_ec2.Port.tcp(2182),
      description='allow msk client to communicate with Apache ZooKeeper by using TLS encryption')
    sg_msk_cluster.add_ingress_rule(peer=sg_msk_client, connection=aws_ec2.Port.tcp(9092),
      description='allow msk client to communicate with brokers in plaintext')
    sg_msk_cluster.add_ingress_rule(peer=sg_msk_client, connection=aws_ec2.Port.tcp(9094),
      description='allow msk client to communicate with brokers by using TLS encryption')
    sg_msk_cluster.add_ingress_rule(peer=sg_msk_client, connection=aws_ec2.Port.tcp(9098),
      description='msk client security group')
    cdk.Tags.of(sg_msk_cluster).add('Name', MSK_CLUSTER_SG_NAME)

    msk_log_group = aws_logs.CfnLogGroup(self, "MSKCloudWatchLogGroup",
      log_group_name=f"/aws/msk/{msk_cluster_name}",
      retention_in_days=7
    )

    msk_cluster = msk.Cluster(self, "MSKCluster",
      cluster_name=msk_cluster_name,
      #XXX: Supported Apache Kafka versions
      # https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html
      # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_msk_alpha/KafkaVersion.html
      kafka_version=msk.KafkaVersion.V2_8_1,
      instance_type=aws_ec2.InstanceType.of(aws_ec2.InstanceClass.M5, aws_ec2.InstanceSize.LARGE),
      number_of_broker_nodes=1, # Number of Apache Kafka brokers deployed in each Availability Zone
      security_groups=[sg_msk_cluster],
      vpc=vpc,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS),
      logging=msk.BrokerLogging(
        cloudwatch_log_group=msk_log_group,
      ),
      monitoring=msk.MonitoringConfiguration(
        cluster_monitoring_level=msk.ClusterMonitoringLevel.PER_TOPIC_PER_BROKER
      ),
      encryption_in_transit=msk.EncryptionInTransitConfig(
        client_broker=msk.ClientBrokerEncryption.TLS_PLAINTEXT
      )
    )

    self.sg_msk_client = sg_msk_client
    self.msk_cluster_arn = msk_cluster.cluster_arn
    self.msk_cluster_name = msk_cluster.cluster_name

    cdk.CfnOutput(self, 'MSKSecurityGroupID', value=sg_msk_cluster.security_group_id,
      export_name=f'{self.stack_name}-ClusterSecurityGroupID')
    cdk.CfnOutput(self, 'KafkaClientSecurityGroupID', value=sg_msk_client.security_group_id,
      export_name=f'{self.stack_name}-ClientSecurityGroupID')
    cdk.CfnOutput(self, 'MSKClusterName', value=self.msk_cluster_name,
      export_name=f'{self.stack_name}-MSKClusterName')
    cdk.CfnOutput(self, 'MSKClusterArn', value=self.msk_cluster_arn,
      export_name=f'{self.stack_name}-MSKClusterArn')