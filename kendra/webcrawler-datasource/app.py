#!/usr/bin/env python3
import os

from cdk_stacks import (
  KendraIndexStack,
  KendraDataSourceStack,
  KendraDataSourceSyncLambdaStack,
  KendraDataSourceSyncStack
)

import aws_cdk as cdk

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

kendra_index = KendraIndexStack(app, "KendraIndexStack",
  env=AWS_ENV)

kendra_data_source = KendraDataSourceStack(app, "KendraDataSourceStack",
  kendra_index_id=kendra_index.kendra_index_id,
  env=AWS_ENV)
kendra_data_source.add_dependency(kendra_index)

kendra_data_source_sync_lambda = KendraDataSourceSyncLambdaStack(app, "KendraDSSyncLambdaStack",
  kendra_index_id=kendra_index.kendra_index_id,
  kendra_data_source_id=kendra_data_source.kendra_data_source_id,
  env=AWS_ENV)
kendra_data_source_sync_lambda.add_dependency(kendra_data_source)

kendra_data_source_sync = KendraDataSourceSyncStack(app, "KendraDSSyncStack",
  kendra_data_source_sync_lambda.kendra_ds_sync_lambda_arn,
  env=AWS_ENV)
kendra_data_source_sync.add_dependency(kendra_data_source_sync_lambda)

app.synth()
