#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

from cdk_stacks import (
  OpsAdminIAMUserStack,
  OpsServerlessVectorSearchStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

ops_admin_user = OpsAdminIAMUserStack(app, "OpsAdminIAMUser")

ops_serverless_vs_stack = OpsServerlessVectorSearchStack(app, "OpsServerlessVectorSearchStack",
  ops_admin_user.user_arn,
  env=AWS_ENV)
ops_serverless_vs_stack.add_dependency(ops_admin_user)

app.synth()
