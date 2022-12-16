#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import random
import string

import aws_cdk as cdk

from aws_cdk import (
	Stack,
  aws_iam,
)
from constructs import Construct

random.seed(47)


class KafkaClientIAMPolicyStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, msk_cluster_name, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

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

    self.kafka_client_iam_policy = kafka_client_iam_policy

    cdk.CfnOutput(self, f'{self.stack_name}-PolicyName',
      value=kafka_client_iam_policy.policy_name,
      export_name=f'{self.stack_name}-PolicyName')
