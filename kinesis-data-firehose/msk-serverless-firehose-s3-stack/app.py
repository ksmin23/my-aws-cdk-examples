#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  KafkaClientEC2InstanceStack,
  MSKServerlessStack,
  MSKClusterPolicyStack,
  KinesisFirehoseStack,
  S3Stack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, 'MSKServerlessVpcStack',
  env=AWS_ENV)

msk_stack = MSKServerlessStack(app, "MSKServerlessStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
msk_stack.add_dependency(vpc_stack)

msk_cluster_policy_stack = MSKClusterPolicyStack(app, "MSKClusterPolicyForFirehose",
  vpc_stack.vpc,
  msk_stack.msk_cluster_name,
  env=AWS_ENV
)
msk_cluster_policy_stack.add_dependency(msk_stack)

kafka_client_ec2_stack = KafkaClientEC2InstanceStack(app, "MSKClientEC2InstanceStack",
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  msk_stack.msk_cluster_name,
  env=AWS_ENV
)
kafka_client_ec2_stack.add_dependency(msk_cluster_policy_stack)

s3_stack = S3Stack(app, "MSKServerlesstoS3AsFirehoseDestinationStack",
  env=AWS_ENV
)
s3_stack.add_dependency(kafka_client_ec2_stack)

firehose_stack = KinesisFirehoseStack(app, 'FirehosefromMSKServerlesstoS3Stack',
  msk_stack.msk_cluster_name,
  msk_stack.msk_cluster_arn,
  s3_stack.s3_bucket,
  env=AWS_ENV
)
firehose_stack.add_dependency(s3_stack)

app.synth()
