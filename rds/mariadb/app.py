#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  MariaDBStack
)

APP_ENV = cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')
)

app = cdk.App()

vpc_stack = VpcStack(app, 'MariaDBVPCStack',
  env=APP_ENV
)

mariadb_stack = MariaDBStack(app, 'MariaDBStack',
  vpc_stack.vpc,
  env=APP_ENV
)
mariadb_stack.add_dependency(vpc_stack)

app.synth()