#!/usr/bin/env python3
import os
import random
import string

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  KafkaClientEC2InstanceStack,
)

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_msk
)
from constructs import Construct

random.seed(47)


class MskServerlessStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    msk_cluster_name = self.node.try_get_context("msk_cluster_name")

    MSK_CLIENT_SG_NAME = 'msk-client-sg-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    sg_msk_client = aws_ec2.SecurityGroup(self, 'KafkaClientSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK client',
      security_group_name=MSK_CLIENT_SG_NAME
    )
    cdk.Tags.of(sg_msk_client).add('Name', MSK_CLIENT_SG_NAME)

    MSK_CLUSTER_SG_NAME = 'msk-cluster-sg-{}'.format(''.join(random.sample((string.ascii_lowercase), k=5)))
    sg_msk_cluster = aws_ec2.SecurityGroup(self, 'MSKSecurityGroup',
      vpc=vpc,
      allow_all_outbound=True,
      description='security group for Amazon MSK Cluster',
      security_group_name=MSK_CLUSTER_SG_NAME
    )
    sg_msk_cluster.add_ingress_rule(peer=sg_msk_client, connection=aws_ec2.Port.tcp(9098),
      description='msk client security group')
    cdk.Tags.of(sg_msk_cluster).add('Name', MSK_CLUSTER_SG_NAME)

    msk_serverless_cluster = aws_msk.CfnServerlessCluster(self, "MSKServerlessCfnCluster",
      #XXX: A serverless cluster must use SASL/IAM authentication
      client_authentication=aws_msk.CfnServerlessCluster.ClientAuthenticationProperty(
        sasl=aws_msk.CfnServerlessCluster.SaslProperty(
          iam=aws_msk.CfnServerlessCluster.IamProperty(
            enabled=True
          )
        )
      ),
      cluster_name=msk_cluster_name,
      vpc_configs=[aws_msk.CfnServerlessCluster.VpcConfigProperty(
        subnet_ids=vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
        security_groups=[sg_msk_client.security_group_id, sg_msk_cluster.security_group_id]
      )]
    )

    self.sg_msk_client = sg_msk_client
    self.msk_cluster_name = msk_serverless_cluster.cluster_name


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'MSKServerlessVpc',
  env=AWS_ENV
)

msk_serverless_stack = MskServerlessStack(app, "MSKServerlessStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
msk_serverless_stack.add_dependency(vpc_stack)

kafka_client_ec2_stack = KafkaClientEC2InstanceStack(app, "MSKClientEC2InstanceStack",
  vpc_stack.vpc,
  msk_serverless_stack.sg_msk_client,
  msk_serverless_stack.msk_cluster_name,
  env=AWS_ENV
)
kafka_client_ec2_stack.add_dependency(msk_serverless_stack)

app.synth()

