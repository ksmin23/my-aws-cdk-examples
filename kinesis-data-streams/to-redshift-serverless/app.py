#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  KdsStack,
  VpcStack,
  RedshiftServerlessStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'KdsToRedshiftVpc',
  env=AWS_ENV)
kds_stack = KdsStack(app, 'KdsToRedshift')
redshift_stack = RedshiftServerlessStack(app, 'RedshiftStreamingStack',
  vpc_stack.vpc)
redshift_stack.add_dependency(vpc_stack)

app.synth()
