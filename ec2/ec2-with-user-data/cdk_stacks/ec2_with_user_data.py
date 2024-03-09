#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
)
from constructs import Construct


class Ec2WithUserDataStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    sg_ec2_instance = aws_ec2.SecurityGroup(self, 'EC2InstanceSG',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for EC2 Instance',
      security_group_name=f'ec2-sg-{self.stack_name.lower()}'
    )
    cdk.Tags.of(sg_ec2_instance).add('Name', 'ec2-sg')
    sg_ec2_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22))

    ec2_instance_role = aws_iam.Role(self, 'EC2InstanceRole',
      role_name=f'EC2InstanceRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        #XXX: EC2 instance should be able to access S3 for user data
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
      ]
    )

    amzn_linux = aws_ec2.MachineImage.latest_amazon_linux2(
      edition=aws_ec2.AmazonLinuxEdition.STANDARD,
      virtualization=aws_ec2.AmazonLinuxVirt.HVM,
      storage=aws_ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
      cpu_type=aws_ec2.AmazonLinuxCpuType.X86_64
    )

    ec2_instance = aws_ec2.Instance(self, 'EC2Instance',
      instance_type=aws_ec2.InstanceType.of(instance_class=aws_ec2.InstanceClass.BURSTABLE3,
        instance_size=aws_ec2.InstanceSize.MICRO),
      machine_image=amzn_linux,
      vpc=vpc,
      availability_zone=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).availability_zones[0],
      instance_name=f'EC2Instance-{self.stack_name}',
      role=ec2_instance_role,
      security_group=sg_ec2_instance,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC)
    )
    ec2_instance.add_security_group(sg_ec2_instance)

    commands = '''
yum -q update -y
yum -q install -y jq
yum -q install java-11 -y

yum groupinstall "Development Tools" -y
yum install -y epel
yum erase -y openssl-devel
yum install -y openssl11-devel
cd /home/ec2-user
wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz
tar xvf Python-3.11.8.tgz
cd Python-3.11.8/
sed -i 's/PKG_CONFIG openssl /PKG_CONFIG openssl11 /g' configure
./configure --enable-optimizations --with-ensurepip=install
make install
cd /home/ec2-user

su -c "/usr/local/bin/python3.11 -m pip install boto3 --user" -s /bin/sh ec2-user
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

echo 'alias aws2=/usr/local/bin/aws' >> .bash_profile
'''

    ec2_instance.user_data.add_commands(commands)


    cdk.CfnOutput(self, 'EC2InstancePublicDNS',
      value=ec2_instance.instance_public_dns_name,
      export_name=f'{self.stack_name}-EC2InstancePublicDNS')
    cdk.CfnOutput(self, 'EC2InstanceId',
      value=ec2_instance.instance_id,
      export_name=f'{self.stack_name}-EC2InstanceId')
    cdk.CfnOutput(self, 'EC2InstanceAZ',
      value=ec2_instance.instance_availability_zone,
      export_name=f'{self.stack_name}-EC2InstanceAZ')