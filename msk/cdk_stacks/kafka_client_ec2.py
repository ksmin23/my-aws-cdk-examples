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
)
from constructs import Construct

random.seed(47)


class KafkaClientEC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, sg_msk_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

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
      machine_image=aws_ec2.MachineImage.latest_amazon_linux2(),
      vpc=vpc,
      availability_zone=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).availability_zones[0],
      instance_name='KafkaClientInstance',
      role=kafka_client_ec2_instance_role,
      security_group=sg_kafka_client_ec2_instance,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )
    msk_client_ec2_instance.add_security_group(sg_msk_client)

    commands = '''
yum update -y
yum install java-1.8.0-openjdk-devel -y

cd /home/ec2-user
mkdir -p opt && cd opt
wget https://archive.apache.org/dist/kafka/3.5.1/kafka_2.12-3.5.1.tgz
tar -xzf kafka_2.12-3.5.1.tgz
ln -nsf kafka_2.12-3.5.1 kafka

cd /home/ec2-user
chown -R ec2-user ./opt
chgrp -R ec2-user ./opt

echo 'export PATH=$HOME/.local/bin:$HOME/opt/kafka/bin:$PATH' >> .bash_profile

cd /home/ec2-user
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

echo 'alias aws=/usr/local/bin/aws' >> .bash_profile
'''

    msk_client_ec2_instance.user_data.add_commands(commands)

    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstancePublicDNS',
      value=msk_client_ec2_instance.instance_public_dns_name,
      export_name=f'{self.stack_name}-EC2InstancePublicDNS')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceId',
      value=msk_client_ec2_instance.instance_id,
      export_name=f'{self.stack_name}-EC2InstanceId')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceAZ',
      value=msk_client_ec2_instance.instance_availability_zone,
      export_name=f'{self.stack_name}-EC2InstanceAZ')

