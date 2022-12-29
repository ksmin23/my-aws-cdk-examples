#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
  aws_s3_assets
)
from constructs import Construct


class OpsClientEC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, opensearch_client_sg, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EC2_KEY_PAIR_NAME = self.node.try_get_context("ec2_key_pair_name")

    ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)

    sg_bastion_host = aws_ec2.SecurityGroup(self, "BastionHostSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an bastion host',
      security_group_name='bastion-host-sg'
    )
    cdk.Tags.of(sg_bastion_host).add('Name', 'bastion-host-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_bastion_host.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"), connection=aws_ec2.Port.tcp(22), description='SSH access')

    ec2_instance_role = aws_iam.Role(self, 'EC2InstanceRole',
      role_name=f'EC2InstanceRole-{self.stack_name}',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        #XXX: EC2 instance should be able to access S3 for user data
        # aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
      ]
    )

    bastion_host = aws_ec2.Instance(self, "BastionHost",
      vpc=vpc,
      instance_type=ec2_instance_type,
      machine_image=aws_ec2.MachineImage.latest_amazon_linux(generation=aws_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=sg_bastion_host,
      role=ec2_instance_role,
      key_name=EC2_KEY_PAIR_NAME
    )
    bastion_host.add_security_group(opensearch_client_sg)

    # test script in S3 as Asset
    user_data_asset = aws_s3_assets.Asset(self, 'OpsClientEC2UserData',
      path=os.path.join(os.path.dirname(__file__), '../src/examples/python/run_opensearch_query.py'))
    user_data_asset.grant_read(bastion_host.role)

    USER_DATA_LOCAL_PATH = bastion_host.user_data.add_s3_download_command(
      bucket=user_data_asset.bucket,
      bucket_key=user_data_asset.s3_object_key,
      local_file='/tmp/run_opensearch_query.py'
    )

    commands = '''
yum update -y
yum install python3.7 -y
yum install -y jq

cd /home/ec2-user
wget https://bootstrap.pypa.io/get-pip.py
su -c "python3.7 get-pip.py --user" -s /bin/sh ec2-user
su -c "/home/ec2-user/.local/bin/pip3 install boto3 --user" -s /bin/sh ec2-user
'''

    commands += f'''
su -c "/home/ec2-user/.local/bin/pip3 install opensearch-py==2.0.1 requests==2.28.1 requests-aws4auth==1.1.2 --user" -s /bin/sh ec2-user
cp {USER_DATA_LOCAL_PATH} /home/ec2-user/run_opensearch_query.py & chown -R ec2-user /home/ec2-user/run_opensearch_query.py
'''

    bastion_host.user_data.add_commands(commands)

    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstancePublicDNS',
      value=bastion_host.instance_public_dns_name,
      export_name=f'{self.stack_name}-EC2InstancePublicDNS')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceId',
      value=bastion_host.instance_id,
      export_name=f'{self.stack_name}-EC2InstanceId')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceAZ',
      value=bastion_host.instance_availability_zone,
      export_name=f'{self.stack_name}-EC2InstanceAZ')

