#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os
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

class MskStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name)

    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    # vpc = aws_ec2.Vpc(self, 'MSKStackVPC',
    #   max_azs=3,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    MSK_CLUSTER_NAME = cdk.CfnParameter(self, 'KafkaClusterName',
      type='String',
      description='Managed Streaming for Apache Kafka cluster name',
      default='MSK-{}'.format(''.join(random.sample((string.ascii_letters), k=5))),
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
      storage_info=msk_broker_storage_info
    )

    msk_encryption_info = aws_msk.CfnCluster.EncryptionInfoProperty(
      encryption_in_transit=aws_msk.CfnCluster.EncryptionInTransitProperty(
        client_broker='TLS_PLAINTEXT',
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
      enhanced_monitoring='PER_TOPIC_PER_BROKER'
    )

    amzn_linux = aws_ec2.MachineImage.latest_amazon_linux(
      generation=aws_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
      edition=aws_ec2.AmazonLinuxEdition.STANDARD,
      virtualization=aws_ec2.AmazonLinuxVirt.HVM,
      storage=aws_ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
      cpu_type=aws_ec2.AmazonLinuxCpuType.X86_64
    )

    KAFKA_CLIENT_EC2_SG_NAME = 'kafka-client-ec2-sg-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    sg_kafka_client_ec2_instance = aws_ec2.SecurityGroup(self, 'KafkaClientEC2InstanceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Kafka Client EC2 Instance',
      security_group_name=KAFKA_CLIENT_EC2_SG_NAME
    )
    cdk.Tags.of(sg_kafka_client_ec2_instance).add('Name', KAFKA_CLIENT_EC2_SG_NAME)
    sg_kafka_client_ec2_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22))

    kafka_client_ec2_instance_role = aws_iam.Role(self, 'KafkaClientEC2InstanceRole',
      role_name='{}-KafkaClientEC2InstanceRole'.format(self.stack_name),
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonMSKReadOnlyAccess')
      ]
    )

    msk_client_ec2_instance = aws_ec2.Instance(self, 'KafkaClientEC2Instance',
      instance_type=aws_ec2.InstanceType.of(instance_class=aws_ec2.InstanceClass.BURSTABLE2,
        instance_size=aws_ec2.InstanceSize.MICRO),
      machine_image=amzn_linux,
      vpc=vpc,
      availability_zone=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).availability_zones[0],
      instance_name='KafkaClientInstance',
      role=kafka_client_ec2_instance_role,
      security_group=sg_kafka_client_ec2_instance,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )
    msk_client_ec2_instance.add_security_group(sg_use_msk)

    commands = '''
yum update -y 
yum install python3.7 -y
yum install java-1.8.0-openjdk-devel -y

cd /home/ec2-user
mkdir -p opt && cd opt
wget https://archive.apache.org/dist/kafka/2.8.1/kafka_2.12-2.8.1.tgz
tar -xzf kafka_2.12-2.8.1.tgz
ln -nsf kafka_2.12-2.8.1 kafka

cd /home/ec2-user
wget https://bootstrap.pypa.io/get-pip.py
su -c "python3.7 get-pip.py --user" -s /bin/sh ec2-user
su -c "/home/ec2-user/.local/bin/pip3 install boto3 --user" -s /bin/sh ec2-user

chown -R ec2-user ./opt
chgrp -R ec2-user ./opt

echo 'export PATH=$HOME/.local/bin:$HOME/opt/kafka/bin:$PATH' >> .bash_profile
'''

    msk_client_ec2_instance.user_data.add_commands(commands)

    cdk.CfnOutput(self, 'StackName', value=self.stack_name, export_name='StackName')
    cdk.CfnOutput(self, 'VpcId', value=vpc.vpc_id, export_name='VpcId')

    cdk.CfnOutput(self, 'MSKSecurityGroupID', value=sg_msk_cluster.security_group_id, export_name='MSKSecurityGroupID')
    cdk.CfnOutput(self, 'KafkaClientSecurityGroupID', value=sg_use_msk.security_group_id, export_name='KafkaClientSecurityGroupID')
    cdk.CfnOutput(self, 'MSKClusterArn', value=msk_cluster.ref, export_name='MSKClusterArn')

    cdk.CfnOutput(self, 'KafkaClientEC2InstancePublicDNS', value=msk_client_ec2_instance.instance_public_dns_name, export_name='KafkaClientEC2InstancePublicDNS')


app = cdk.App()
MskStack(app, 'MSKStack',
  env=cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
