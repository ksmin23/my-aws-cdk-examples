#!/usr/bin/env python3
import os

from cdk_stacks import (
  OpsAdminIAMUserStack,
  OpsServerlessTimeSeriesStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

ops_admin_user = OpsAdminIAMUserStack(app, "OpsAdminIAMUser")

ops_serverless_ts_stack = OpsServerlessTimeSeriesStack(app, "OpsServerlessTSStack",
  ops_admin_user.user_arn,
  env=AWS_ENV)
ops_serverless_ts_stack.add_dependency(ops_admin_user)

app.synth()
