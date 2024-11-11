#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_logs,
  aws_msk
)
from constructs import Construct

random.seed(47)

class MSKProvisionedStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    msk_configuration = self.node.try_get_context('msk_configuration')
    MSK_DEFAULT_CLUSTER_NAME = 'MSK-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    MSK_CLUSTER_NAME = msk_configuration.get('kafka_cluster_name', MSK_DEFAULT_CLUSTER_NAME)

    # Supported Apache Kafka versions
    # https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html
    KAFA_VERSION = msk_configuration.get('kafka_version', '3.6.0')

    KAFA_BROKER_INSTANCE_TYPE = msk_configuration.get('kafka_broker_instance_type', 'express.m7g.large')

    KAFA_BROKER_EBS_VOLUME_SIZE = int(msk_configuration.get('kafka_broker_ebs_volume_size', '100'))
    assert (1 <= KAFA_BROKER_EBS_VOLUME_SIZE and KAFA_BROKER_EBS_VOLUME_SIZE <= 16384), 'Apache Kafka Broker EBS Volume size (Minimum: 1 GiB, Maximum: 16384 GiB)'

    MSK_CLIENT_SG_NAME = f'msk-client-sg-{MSK_CLUSTER_NAME}'
    sg_msk_client = aws_ec2.SecurityGroup(self, 'KafkaClientSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK client',
      security_group_name=MSK_CLIENT_SG_NAME
    )
    cdk.Tags.of(sg_msk_client).add('Name', MSK_CLIENT_SG_NAME)

    MSK_CLUSTER_SG_NAME = f'msk-cluster-sg-{MSK_CLUSTER_NAME}'
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

    if KAFA_BROKER_INSTANCE_TYPE.startswith('express.'):
      #XXX: The storageInfo parameter is not supported for Express instance types.
      msk_broker_storage_info = None
    else:
      msk_broker_storage_info = aws_msk.CfnCluster.StorageInfoProperty(
        ebs_storage_info=aws_msk.CfnCluster.EBSStorageInfoProperty(
          volume_size=KAFA_BROKER_EBS_VOLUME_SIZE
        )
      )

    msk_broker_node_group_info = aws_msk.CfnCluster.BrokerNodeGroupInfoProperty(
      client_subnets=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      instance_type=KAFA_BROKER_INSTANCE_TYPE,
      security_groups=[sg_msk_client.security_group_id, sg_msk_cluster.security_group_id],
      storage_info=msk_broker_storage_info
    )

    msk_encryption_info = aws_msk.CfnCluster.EncryptionInfoProperty(
      encryption_in_transit=aws_msk.CfnCluster.EncryptionInTransitProperty(
        client_broker='TLS_PLAINTEXT',
        in_cluster=True
      )
    )

    if KAFA_BROKER_INSTANCE_TYPE.startswith('express.'):
      msk_logging_info = None
    else:
      #XXX: Broker logs are not supported for clusters with Express instance types.
      msk_log_group = aws_logs.CfnLogGroup(self, 'MSKCloudWatchLogGroup',
        log_group_name=f"/aws/msk/{MSK_CLUSTER_NAME}",
        retention_in_days=7
      )
      msk_log_group.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

      msk_logging_info = aws_msk.CfnCluster.LoggingInfoProperty(
        broker_logs=aws_msk.CfnCluster.BrokerLogsProperty(
          cloud_watch_logs=aws_msk.CfnCluster.CloudWatchLogsProperty(
            enabled=True,
            log_group=msk_log_group.log_group_name
          )
        )
      )

    msk_cluster = aws_msk.CfnCluster(self, 'AWSKafkaCluster',
      broker_node_group_info=msk_broker_node_group_info,
      cluster_name=MSK_CLUSTER_NAME,
      #XXX: Supported Apache Kafka versions
      # https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html
      kafka_version=KAFA_VERSION,
      number_of_broker_nodes=3,
      encryption_info=msk_encryption_info,
      enhanced_monitoring='PER_TOPIC_PER_BROKER',
      logging_info=msk_logging_info
    )

    self.sg_msk_client = sg_msk_client

    cdk.CfnOutput(self, 'MSKSecurityGroupID', value=sg_msk_cluster.security_group_id,
      export_name=f'{self.stack_name}-ClusterSecurityGroupID')
    cdk.CfnOutput(self, 'KafkaClientSecurityGroupID', value=sg_msk_client.security_group_id,
      export_name=f'{self.stack_name}-ClientSecurityGroupID')
    cdk.CfnOutput(self, 'MSKClusterArn', value=msk_cluster.ref,
      export_name=f'{self.stack_name}-MSKClusterArn')

