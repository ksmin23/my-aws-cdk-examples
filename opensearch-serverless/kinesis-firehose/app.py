#!/usr/bin/env python3
import os

from cdk_stacks import (
  OpsAdminIAMUserStack,
  OpsServerlessTimeSeriesStack,
  KinesisFirehoseS3Stack,
  KinesisFirehoseRoleStack,
  KinesisFirehoseStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

s3_stack = KinesisFirehoseS3Stack(app, "FirehoseS3Stack",
  env=AWS_ENV
)

firehose_role_stack = KinesisFirehoseRoleStack(app, "FirehoseRole",
  s3_stack.s3_bucket_arn,
  env=AWS_ENV
)
firehose_role_stack.add_dependency(s3_stack)

ops_admin_user = OpsAdminIAMUserStack(app, "OpsAdminIAMUser")

ops_serverless_stack = OpsServerlessTimeSeriesStack(app, "OpsServerlessTSStack",
  ops_admin_user.user_arn,
  firehose_role_stack.firehose_role_name,
  env=AWS_ENV
)
ops_serverless_stack.add_dependency(ops_admin_user)
ops_serverless_stack.add_dependency(firehose_role_stack)

firehose_stack = KinesisFirehoseStack(app, "FirehoseToOpsServerlessStack",
  firehose_role_stack.firehose_role_arn,
  ops_serverless_stack.opensearch_endpoint,
  s3_stack.s3_bucket_arn,
  env=AWS_ENV
)
firehose_stack.add_dependency(ops_serverless_stack)
firehose_stack.add_dependency(s3_stack)

app.synth()
