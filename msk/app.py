#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from aws_cdk import (
  core as cdk,
  aws_ec2,
  aws_iam,
  aws_logs,
  aws_msk
)


class MskStack(cdk.Stack):

  def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # The code that defines your stack goes here
    vpc_name = self.node.try_get_context('vpc_name')
    vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
      is_default=True,
      vpc_name=vpc_name)

    sg_use_msk = aws_ec2.SecurityGroup(self, 'KafkaClientSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK client',
      security_group_name='use-msk-tutorial-sg'
    )
    cdk.Tags.of(sg_use_msk).add('Name', 'use-msk-tutorial-sg')

    sg_msk_cluster = aws_ec2.SecurityGroup(self, 'MSKSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK Cluster',
      security_group_name='msk-tutorial-sg'
    )
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(2181),
      description='use-msk-tutorial-sg')
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(9092),
      description='use-msk-tutorial-sg')
    sg_msk_cluster.add_ingress_rule(peer=sg_use_msk, connection=aws_ec2.Port.tcp(9094),
      description='use-msk-tutorial-sg')
    cdk.Tags.of(sg_msk_cluster).add('Name', 'msk-tutorial-sg')

    #XXX: change volume size
    msk_broker_ebs_storage_info = aws_msk.CfnCluster.EBSStorageInfoProperty(volume_size=100)

    msk_broker_storage_info = aws_msk.CfnCluster.StorageInfoProperty(
      ebs_storage_info=msk_broker_ebs_storage_info
    )
    
    msk_broker_node_group_info = aws_msk.CfnCluster.BrokerNodeGroupInfoProperty(
      client_subnets=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE).subnet_ids,
      instance_type='kafka.m5.large', #XXX: change broker instance type 
      security_groups=[sg_use_msk.security_group_id, sg_msk_cluster.security_group_id],
      storage_info=msk_broker_storage_info
    )

    msk_encryption_info = aws_msk.CfnCluster.EncryptionInfoProperty(
      encryption_in_transit=aws_msk.CfnCluster.EncryptionInTransitProperty(
        client_broker='TLS_PLAINTEXT',
        in_cluster=True
      )
    )

    msk_cluster_name = self.node.try_get_context('kafka_cluster_name')
    msk_cluster = aws_msk.CfnCluster(self, 'AWSKafkaCluster',
      broker_node_group_info=msk_broker_node_group_info,
      cluster_name=msk_cluster_name,
      kafka_version='2.6.1',
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

    sg_kafka_client_ec2_instance = aws_ec2.SecurityGroup(self, 'KafkaClientEC2InstanceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Kafka Client EC2 Instance',
      security_group_name='kafka-client-ec2-sg'
    )
    cdk.Tags.of(sg_kafka_client_ec2_instance).add('Name', 'kafka-client-ec2-sg')
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
      availability_zone=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE).availability_zones[0],
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
echo "export PATH=.local/bin:$PATH" >> .bash_profile

mkdir -p opt
cd opt
wget https://archive.apache.org/dist/kafka/2.2.1/kafka_2.12-2.2.1.tgz
tar -xzf kafka_2.12-2.2.1.tgz
ln -nsf kafka_2.12-2.2.1 kafka

cd /home/ec2-user
wget https://bootstrap.pypa.io/get-pip.py
su -c "python3.7 get-pip.py --user" -s /bin/sh ec2-user
su -c "/home/ec2-user/.local/bin/pip3 install boto3 --user" -s /bin/sh ec2-user

chown -R ec2-user ./opt
chgrp -R ec2-user ./opt
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
