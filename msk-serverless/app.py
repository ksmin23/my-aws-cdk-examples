#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  KafkaClientEC2InstanceStack,
  MskServerlessStack
)


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

kafka_client_ec2_stack = KafkaClientEC2InstanceStack(app, "MSKServerlessClientEC2Stack",
  vpc_stack.vpc,
  msk_serverless_stack.sg_msk_client,
  msk_serverless_stack.msk_cluster_name,
  env=AWS_ENV
)
kafka_client_ec2_stack.add_dependency(msk_serverless_stack)

app.synth()

