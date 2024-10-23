#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  DataLakePermissionsStack,
  FirehoseToIcebergStack,
  FirehoseRoleStack,
  FirehoseDataProcLambdaStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

firehose_data_transform_lambda = FirehoseDataProcLambdaStack(app,
  'FirehoseDataTransformLambdaStack',
  env=AWS_ENV
)

firehose_role = FirehoseRoleStack(app, 'FirehoseToIcebergRoleStack',
  firehose_data_transform_lambda.data_proc_lambda_fn,
  env=AWS_ENV
)
firehose_role.add_dependency(firehose_data_transform_lambda)

grant_lake_formation_permissions = DataLakePermissionsStack(app, 'GrantLFPermissionsOnFirehoseRole',
  firehose_role.firehose_role,
  env=AWS_ENV
)
grant_lake_formation_permissions.add_dependency(firehose_role)

firehose_stack = FirehoseToIcebergStack(app, 'FirehoseToIcebergStack',
  firehose_data_transform_lambda.data_proc_lambda_fn,
  firehose_role.firehose_role,
  env=AWS_ENV
)
firehose_stack.add_dependency(grant_lake_formation_permissions)

app.synth()
