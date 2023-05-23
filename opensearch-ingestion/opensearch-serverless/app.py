#!/usr/bin/env python3
import os

from cdk_stacks import (
  OpsCollectionPipelineRoleStack,
  OpsServerlessTimeSeriesStack,
  OpsServerlessIngestionStack
)

import aws_cdk as cdk


AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

collection_pipeline_role = OpsCollectionPipelineRoleStack(app, 'OpsCollectionPipelineRoleStack')

ops_serverless_ts_stack = OpsServerlessTimeSeriesStack(app, "OpsServerlessTSStack",
  collection_pipeline_role.iam_role.role_arn,
  env=AWS_ENV)
ops_serverless_ts_stack.add_dependency(collection_pipeline_role)

ops_serverless_ingestion_stack = OpsServerlessIngestionStack(app, "OpsServerlessIngestionStack",
  ops_serverless_ts_stack.collection_endpoint,
  env=AWS_ENV)
ops_serverless_ingestion_stack.add_dependency(ops_serverless_ts_stack)

app.synth()
