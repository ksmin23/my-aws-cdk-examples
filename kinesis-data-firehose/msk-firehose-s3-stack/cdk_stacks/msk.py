#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_msk
)
from constructs import Construct

random.seed(47)

class MSKProvisionedStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    MSK_CLUSTER_NAME = cdk.CfnParameter(self, 'KafkaClusterName',
      type='String',
      description='Managed Streaming for Apache Kafka cluster name',
      default='msk-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5))),
      allowed_pattern='[A-Za-z0-9\-]+'
    )

    KAFA_VERSION = cdk.CfnParameter(self, 'KafkaVersion',
      type='String',
      description='Apache Kafka version',
      default='2.8.1',
      # Supported Apache Kafka versions
      # https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html
      allowed_values=[
        '3.3.1',
        '3.2.0',
        '2.8.2',
        '2.8.1', # recommended
        '2.8.0',
        '2.7.1',
        '2.6.2',
        '2.6.1',
        '2.6.0',
        '2.5.1',
        '2.4.1.1',
        '2.3.1',
        '2.2.1'
      ]
    )

    #XXX: change broker instance type
    KAFA_BROKER_INSTANCE_TYPE = cdk.CfnParameter(self, 'KafkaBrokerInstanceType',
      type='String',
      description='Apache Kafka Broker instance type',
      default='kafka.m5.large'
    )

    #XXX: change volume size
    KAFA_BROKER_EBS_VOLUME_SIZE = cdk.CfnParameter(self, 'KafkaBrokerEBSVolumeSize',
      type='Number',
      description='Apache Kafka Broker EBS Volume size (Minimum: 1 GiB, Maximum: 16384 GiB)',
      default='100',
      min_value=1,
      max_value=16384
    )

    MSK_CLIENT_SG_NAME = 'use-msk-sg-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    sg_use_msk = aws_ec2.SecurityGroup(self, 'KafkaClientSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK client',
      security_group_name=MSK_CLIENT_SG_NAME
    )
    cdk.Tags.of(sg_use_msk).add('Name', MSK_CLIENT_SG_NAME)

    MSK_CLUSTER_SG_NAME = 'msk-sg-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    sg_msk_cluster = aws_ec2.SecurityGroup(self, 'MSKSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK Cluster',
      security_group_name=MSK_CLUSTER_SG_NAME
    )
    # For more information about the numbers of the ports that Amazon MSK uses to communicate with client machines,
    # see https://docs.aws.amazon.com/msk/latest/developerguide/port-info.html
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(2181),
      description='allow msk client to communicate with Apache ZooKeeper in plaintext')
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(2182),
      description='allow msk client to communicate with Apache ZooKeeper by using TLS encryption')
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(9092),
      description='allow msk client to communicate with brokers in plaintext')
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(9094),
      description='allow msk client to communicate with brokers by using TLS encryption')
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(9098),
      description='msk client security group')
    cdk.Tags.of(sg_msk_cluster).add('Name', MSK_CLUSTER_SG_NAME)


    msk_broker_ebs_storage_info = aws_msk.CfnCluster.EBSStorageInfoProperty(volume_size=KAFA_BROKER_EBS_VOLUME_SIZE.value_as_number)

    msk_broker_storage_info = aws_msk.CfnCluster.StorageInfoProperty(
      ebs_storage_info=msk_broker_ebs_storage_info
    )

    msk_broker_node_group_info = aws_msk.CfnCluster.BrokerNodeGroupInfoProperty(
      client_subnets=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
      instance_type=KAFA_BROKER_INSTANCE_TYPE.value_as_string,
      security_groups=[sg_use_msk.security_group_id, sg_msk_cluster.security_group_id],
      storage_info=msk_broker_storage_info,
      #XXX: When creating a cluster, all vpcConnectivity auth schemes must be disabled.
      # You can enable auth schemes after the cluster is created.
      #
      # connectivity_info=aws_msk.CfnCluster.ConnectivityInfoProperty(
      #   public_access=aws_msk.CfnCluster.PublicAccessProperty(
      #     type="DISABLED" # [DISABLED|SERVICE_PROVIDED_EIPS]
      #   ),
      #   #XXX: Only client broker communication over TLS is supported for clusters with multi-VPC private connectivity turned on.
      #   vpc_connectivity=aws_msk.CfnCluster.VpcConnectivityProperty(
      #     client_authentication=aws_msk.CfnCluster.VpcConnectivityClientAuthenticationProperty(
      #       sasl=aws_msk.CfnCluster.VpcConnectivitySaslProperty(
      #         iam=aws_msk.CfnCluster.VpcConnectivityIamProperty(
      #           enabled=True)))))
    )

    msk_encryption_info = aws_msk.CfnCluster.EncryptionInfoProperty(
      encryption_in_transit=aws_msk.CfnCluster.EncryptionInTransitProperty(
        client_broker='TLS', # ['PLAINTEXT' | 'TLS' | 'TLS_PLAINTEXT']
        in_cluster=True
      )
    )

    msk_cluster = aws_msk.CfnCluster(self, 'AWSKafkaCluster',
      broker_node_group_info=msk_broker_node_group_info,
      cluster_name=MSK_CLUSTER_NAME.value_as_string,
      #XXX: Supported Apache Kafka versions
      # https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html
      kafka_version=KAFA_VERSION.value_as_string,
      number_of_broker_nodes=3,
      encryption_info=msk_encryption_info,
      enhanced_monitoring='PER_TOPIC_PER_BROKER',
      #XXX: When creating a cluster, all vpcConnectivity auth schemes must be disabled.
      # You can enable auth schemes after the cluster is created.
      #
      # client_authentication=aws_msk.CfnCluster.ClientAuthenticationProperty(
      #   sasl=aws_msk.CfnCluster.SaslProperty(
      #     iam=aws_msk.CfnCluster.IamProperty(
      #       enabled=True
      #     )
      #   ),
      #   #XXX: You must enable unauthenticated traffic explicitly to use client-authentication using SASL over TLS_PLAINTEXT
      #   unauthenticated=aws_msk.CfnCluster.UnauthenticatedProperty(
      #     enabled=False
      #   )
      # )
    )

    self.sg_msk_client = sg_use_msk
    self.msk_cluster_arn = msk_cluster.ref
    self.msk_cluster_name = msk_cluster.cluster_name

    cdk.CfnOutput(self, 'MSKSecurityGroupID', value=sg_msk_cluster.security_group_id,
      export_name=f'{self.stack_name}-ClusterSecurityGroupID')
    cdk.CfnOutput(self, 'KafkaClientSecurityGroupID', value=sg_use_msk.security_group_id,
      export_name=f'{self.stack_name}-ClientSecurityGroupID')
    cdk.CfnOutput(self, 'MSKClusterArn', value=msk_cluster.ref,
      export_name=f'{self.stack_name}-MSKClusterArn')
    cdk.CfnOutput(self, 'MSKClusterName', value=self.msk_cluster_name,
      export_name=f'{self.stack_name}-MSKClusterName')
