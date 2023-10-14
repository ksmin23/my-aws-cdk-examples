#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam,
)
from constructs import Construct


class DLAMIEC2InstanceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    EC2_INSTANCE_TYPE = self.node.try_get_context('instance_type') or 'g4dn.xlarge'

    dlami_name = self.node.try_get_context('dlami_name')

    sg_dlami_instance = aws_ec2.SecurityGroup(self, "DLInstanceSG",
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for an Deep Learning instance',
      security_group_name='dl-instance-sg'
    )
    cdk.Tags.of(sg_dlami_instance).add('Name', 'dl-instance-sg')

    #TODO: SHOULD restrict IP range allowed to ssh acces
    sg_dlami_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(22), description='SSH access')
    sg_dlami_instance.add_ingress_rule(peer=aws_ec2.Peer.ipv4("0.0.0.0/0"),
      connection=aws_ec2.Port.tcp(8888), description='Jupyter Notebook access')

    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceClass.html
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/InstanceSize.html#aws_cdk.aws_ec2.InstanceSize
    # ec2_instance_type = aws_ec2.InstanceType.of(aws_ec2.InstanceClass.BURSTABLE3, aws_ec2.InstanceSize.MEDIUM)
    ec2_instance_type = aws_ec2.InstanceType(EC2_INSTANCE_TYPE)

    #XXX: Release Notes for DLAMI
    # https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html
    ec2_machine_image = aws_ec2.MachineImage.lookup(
      name=dlami_name,
      owners=["amazon"]
    )

    dlami_instance_role = aws_iam.Role(self, 'DLInstanceSSMRole',
      role_name=f'{self.stack_name}-EC2InstanceRole',
      assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
        #XXX: EC2 instance should be able to access S3 for user data
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
      ]
    )

    dlami_instance = aws_ec2.Instance(self, "DLInstance",
      vpc=vpc,
      role=dlami_instance_role,
      instance_type=ec2_instance_type,
      machine_image=ec2_machine_image,
      vpc_subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
      security_group=sg_dlami_instance
    )

    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstancePublicDNS',
      value=dlami_instance.instance_public_dns_name,
      export_name=f'{self.stack_name}-EC2InstancePublicDNS')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceId',
      value=dlami_instance.instance_id,
      export_name=f'{self.stack_name}-EC2InstanceId')
    cdk.CfnOutput(self, f'{self.stack_name}-EC2InstanceAZ',
      value=dlami_instance.instance_availability_zone,
      export_name=f'{self.stack_name}-EC2InstanceAZ')
