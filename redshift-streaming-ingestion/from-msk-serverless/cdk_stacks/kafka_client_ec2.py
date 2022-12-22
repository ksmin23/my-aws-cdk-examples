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
  aws_s3_assets
)
from constructs import Construct

random.seed(37)


class KafkaClientEC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, sg_msk_client, msk_cluster_name, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    KAFKA_CLIENT_EC2_SG_NAME = 'kafka-client-ec2-sg-{}'.format(''.join(random.choices((string.ascii_lowercase), k=5)))
    sg_kafka_client_ec2_instance = aws_ec2.SecurityGroup(self, 'KafkaClientEC2InstanceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Kafka Client EC2 Instance',
      security_group_name=KAFKA_CLIENT_EC2_SG_NAME
    )
    cdk.Tags.of(sg_kafka_client_ec2_instance).add('Name', KAFKA_CLIENT_EC2_SG_NAME)
    sg_kafka_client_ec2_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22))

    #XXX: For more information, see https://docs.aws.amazon.com/msk/latest/developerguide/create-iam-role.html
    kafka_client_iam_policy = aws_iam.Policy(self, 'KafkaClientIAMPolicy',
      statements=[
        aws_iam.PolicyStatement(**{
          "effect": aws_iam.Effect.ALLOW,
          "resources": [ f"arn:aws:kafka:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:cluster/{msk_cluster_name}/*" ],
          "actions": [
            "kafka-cluster:Connect",
            "kafka-cluster:AlterCluster",
            "kafka-cluster:DescribeCluster"
          ]
        }),
        aws_iam.PolicyStatement(**{
          "effect": aws_iam.Effect.ALLOW,
          "resources": [ f"arn:aws:kafka:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:topic/{msk_cluster_name}/*" ],
          "actions": [
            "kafka-cluster:*Topic*",
            "kafka-cluster:WriteData",
            "kafka-cluster:ReadData"
          ]
        }),
        aws_iam.PolicyStatement(**{
          "effect": aws_iam.Effect.ALLOW,
          "resources": [ f"arn:aws:kafka:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:group/{msk_cluster_name}/*" ],
          "actions": [
            "kafka-cluster:AlterGroup",
            "kafka-cluster:DescribeGroup"
          ]
        })
      ]
    )
    kafka_client_iam_policy.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    kafka_client_ec2_instance_role = aws_iam.Role(self, 'KafkaClientEC2InstanceRole',
      role_name=f'KafkaClientEC2InstanceRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        #XXX: EC2 instance should be able to access S3 for user data
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
      ]
    )

    kafka_client_iam_policy.attach_to_role(kafka_client_ec2_instance_role)

    amzn_linux = aws_ec2.MachineImage.latest_amazon_linux(
      generation=aws_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
      edition=aws_ec2.AmazonLinuxEdition.STANDARD,
      virtualization=aws_ec2.AmazonLinuxVirt.HVM,
      storage=aws_ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
      cpu_type=aws_ec2.AmazonLinuxCpuType.X86_64
    )

    msk_client_ec2_instance = aws_ec2.Instance(self, 'KafkaClientEC2Instance',
      instance_type=aws_ec2.InstanceType.of(instance_class=aws_ec2.InstanceClass.BURSTABLE2,
        instance_size=aws_ec2.InstanceSize.MICRO),
      machine_image=amzn_linux,
      vpc=vpc,
      availability_zone=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).availability_zones[0],
      instance_name=f'KafkaClientInstance-{self.stack_name}',
      role=kafka_client_ec2_instance_role,
      security_group=sg_kafka_client_ec2_instance,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )
    msk_client_ec2_instance.add_security_group(sg_msk_client)

    # test data generator script in S3 as Asset
    user_data_asset = aws_s3_assets.Asset(self, 'KafkaClientEC2UserData',
      path=os.path.join(os.path.dirname(__file__), '../src/main/python/gen_fake_data.py'))

    USER_DATA_LOCAL_PATH = msk_client_ec2_instance.user_data.add_s3_download_command(
      bucket=user_data_asset.bucket,
      bucket_key=user_data_asset.s3_object_key
    )

    commands = '''
yum update -y 
yum install python3.7 -y
yum install java-11 -y
yum install -y jq

mkdir -p /home/ec2-user/opt
cd /home/ec2-user/opt
wget https://archive.apache.org/dist/kafka/2.8.1/kafka_2.12-2.8.1.tgz
tar -xzf kafka_2.12-2.8.1.tgz
ln -nsf kafka_2.12-2.8.1 kafka

cd /home/ec2-user/opt/kafka/libs
wget https://github.com/aws/aws-msk-iam-auth/releases/download/v1.1.1/aws-msk-iam-auth-1.1.1-all.jar

chown -R ec2-user /home/ec2-user/opt
chgrp -R ec2-user /home/ec2-user/opt

cd /home/ec2-user
wget https://bootstrap.pypa.io/get-pip.py
su -c "python3.7 get-pip.py --user" -s /bin/sh ec2-user
su -c "/home/ec2-user/.local/bin/pip3 install boto3 --user" -s /bin/sh ec2-user

cat <<EOF > msk_serverless_client.properties
security.protocol=SASL_SSL
sasl.mechanism=AWS_MSK_IAM
sasl.jaas.config=software.amazon.msk.auth.iam.IAMLoginModule required;
sasl.client.callback.handler.class=software.amazon.msk.auth.iam.IAMClientCallbackHandler
EOF

ln -nsf msk_serverless_client.properties client.properties
chown -R ec2-user /home/ec2-user/msk_serverless_client.properties
chown -R ec2-user /home/ec2-user/client.properties

echo 'export PATH=$HOME/opt/kafka/bin:$PATH' >> .bash_profile
'''

    commands += f'''
su -c "/home/ec2-user/.local/bin/pip3 install mimesis==4.1.3 --user" -s /bin/sh ec2-user
cp {USER_DATA_LOCAL_PATH} /home/ec2-user/gen_fake_data.py & chown -R ec2-user /home/ec2-user/gen_fake_data.py
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

