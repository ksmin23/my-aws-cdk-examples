#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  MskServerlessStack,
  KafkaClientEC2InstanceStack,
  RedshiftServerlessStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'MSKServerlessToRedshiftVpc',
  env=AWS_ENV
)

msk_stack = MskServerlessStack(app, 'MSKServerlessToRedshiftServerless',
  vpc_stack.vpc,
  env=AWS_ENV
)
msk_stack.add_dependency(vpc_stack)

redshift_stack = RedshiftServerlessStack(app, 'RedshiftStreamingFromMSKServerless',
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  env=AWS_ENV
)
redshift_stack.add_dependency(msk_stack)

kafka_client_ec2_stack = KafkaClientEC2InstanceStack(app, 'MSKServerlessClientEC2Stack',
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  msk_stack.msk_cluster_name,
  env=AWS_ENV
)
kafka_client_ec2_stack.add_dependency(msk_stack)

app.synth()

