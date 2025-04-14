#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  DataLakePermissionsStack,
  FirehoseToS3TablesStack,
  FirehoseRoleStack,
  GlueDatabaseForS3TablesStack,
  S3BucketStack,
  S3TablesStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

s3table_bucket = S3TablesStack(app, 'FirehoseToS3TablesTableBucket',
  env=AWS_ENV)

s3table_resource_link = GlueDatabaseForS3TablesStack(app, 'FirehoseToS3TablesResourceLink',
  s3table_bucket.table_bucket_name,
  env=AWS_ENV)
s3table_resource_link.add_dependency(s3table_bucket)

s3_error_output_bucket = S3BucketStack(app, 'FirehoseToS3TablesS3ErrorOutputPath',
  env=AWS_ENV)
s3_error_output_bucket.add_dependency(s3table_resource_link)

firehose_role = FirehoseRoleStack(app, 'FirehoseToS3TablesRole',
  s3_error_output_bucket.s3_bucket,
  env=AWS_ENV
)
firehose_role.add_dependency(s3_error_output_bucket)

grant_lf_permissions = DataLakePermissionsStack(app, 'FirehoseToS3TablesGrantLFPermissionsOnFirehoseRole',
  s3table_bucket.table_bucket_name,
  firehose_role.firehose_role,
  s3table_resource_link.s3table_resource_link,
  env=AWS_ENV
)
grant_lf_permissions.add_dependency(firehose_role)

firehose_stack = FirehoseToS3TablesStack(app, 'FirehoseToS3TablesDeliveryStream',
  s3_error_output_bucket.s3_bucket,
  firehose_role.firehose_role,
  env=AWS_ENV
)
firehose_stack.add_dependency(grant_lf_permissions)

app.synth()
