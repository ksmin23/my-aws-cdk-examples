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

random.seed(47)


class DocDBClientEC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, sg_docdb_client, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    DOCDB_CLIENT_EC2_SG_NAME = 'docdb-client-ec2-sg-{}'.format(''.join(random.choices((string.ascii_lowercase), k=5)))
    sg_docdb_client_ec2_instance = aws_ec2.SecurityGroup(self, 'DocDBClientEC2InstanceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for DocumentDB Client EC2 Instance',
      security_group_name=DOCDB_CLIENT_EC2_SG_NAME
    )
    cdk.Tags.of(sg_docdb_client_ec2_instance).add('Name', DOCDB_CLIENT_EC2_SG_NAME)
    sg_docdb_client_ec2_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22))

    secretmanager_readonly_access_policy_doc = aws_iam.PolicyDocument()
    secretmanager_readonly_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ],
      "resources": [ "arn:aws:secretsmanager:*:*:secret:*" ]
    }))

    secretmanager_readonly_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "actions": [
        "secretsmanager:ListSecrets"
      ],
      "resources": [ "*" ]
    }))

    docdb_client_ec2_instance_role = aws_iam.Role(self, 'DocDBClientEC2InstanceRole',
      role_name=f'DocDBClientEC2InstanceRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      inline_policies={
        'SecretsManagerReadOnlyAccessPolicy': secretmanager_readonly_access_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDocDBReadOnlyAccess')
      ]
    )

    amzn_linux = aws_ec2.MachineImage.latest_amazon_linux(
      generation=aws_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
      edition=aws_ec2.AmazonLinuxEdition.STANDARD,
      virtualization=aws_ec2.AmazonLinuxVirt.HVM,
      storage=aws_ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
      cpu_type=aws_ec2.AmazonLinuxCpuType.X86_64
    )

    docdb_client_ec2_instance = aws_ec2.Instance(self, 'DocDBClientEC2Instance',
      instance_type=aws_ec2.InstanceType.of(instance_class=aws_ec2.InstanceClass.BURSTABLE2,
        instance_size=aws_ec2.InstanceSize.MICRO),
      machine_image=amzn_linux,
      vpc=vpc,
      availability_zone=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).availability_zones[0],
      instance_name='DocDBClientInstance',
      role=docdb_client_ec2_instance_role,
      security_group=sg_docdb_client_ec2_instance,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )
    docdb_client_ec2_instance.add_security_group(sg_docdb_client)

    commands = '''
cat <<EOF > /etc/yum.repos.d/mongodb-org-4.0.repo
[mongodb-org-4.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2013.03/mongodb-org/4.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.0.asc
EOF

yum install -y mongodb-org-shell

yum install -y jq
yum install python3.7 -y

cd /home/ec2-user
wget https://bootstrap.pypa.io/get-pip.py
su -c "python3.7 get-pip.py --user" -s /bin/sh ec2-user
su -c "/home/ec2-user/.local/bin/pip3 install boto3 pymongo --user" -s /bin/sh ec2-user
'''

    docdb_client_ec2_instance.user_data.add_commands(commands)

    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstancePublicDNS',
      value=docdb_client_ec2_instance.instance_public_dns_name,
      export_name=f'{self.stack_name}-EC2InstancePublicDNS')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceId',
      value=docdb_client_ec2_instance.instance_id,
      export_name=f'{self.stack_name}-EC2InstanceId')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceAZ',
      value=docdb_client_ec2_instance.instance_availability_zone,
      export_name=f'{self.stack_name}-EC2InstanceAZ')

