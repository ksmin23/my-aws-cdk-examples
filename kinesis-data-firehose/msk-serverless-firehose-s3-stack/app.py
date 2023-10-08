#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  KafkaClientEC2InstanceStack,
  MSKServerlessStack,
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

kafka_client_ec2_stack = KafkaClientEC2InstanceStack(app, "MSKClientEC2InstanceStack",
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  msk_stack.msk_cluster_name,
  env=AWS_ENV
)
kafka_client_ec2_stack.add_dependency(msk_stack)

s3_stack = S3Stack(app, "MSKServerlessToS3Stack",
  env=AWS_ENV
)
s3_stack.add_dependency(kafka_client_ec2_stack)

app.synth()
