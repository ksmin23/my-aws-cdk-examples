#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  DeltalakeConnectionStack,
  KdsStack,
  GlueJobRoleStack,
  GlueStreamDataSchemaStack,
  GlueStreamingJobStack,
  DataLakePermissionsStack,
  S3BucketStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))


app = cdk.App()

s3_bucket = S3BucketStack(app, 'DeltalakeS3Path')

kds_stack = KdsStack(app, 'KinesisStreamAsGlueStreamingJobDataSource')
kds_stack.add_dependency(s3_bucket)

glue_job_role = GlueJobRoleStack(app, 'GlueStreamingSinkToDeltalakeJobRole')
glue_job_role.add_dependency(kds_stack)

glue_stream_schema = GlueStreamDataSchemaStack(app, 'GlueSchemaOnKinesisStream',
  kds_stack.kinesis_stream
)
glue_stream_schema.add_dependency(kds_stack)

grant_lake_formation_permissions = DataLakePermissionsStack(app, 'GrantLFPermissionsOnGlueJobRole',
  glue_job_role.glue_job_role
)
grant_lake_formation_permissions.add_dependency(glue_job_role)
grant_lake_formation_permissions.add_dependency(glue_stream_schema)

deltalake_conn = DeltalakeConnectionStack(app, "SinkToDeltalakeConnectionStack")
deltalake_conn.add_dependency(grant_lake_formation_permissions)

glue_streaming_job = GlueStreamingJobStack(app, 'GlueStreamingSinkToDeltalake',
  glue_job_role.glue_job_role,
  kds_stack.kinesis_stream
)
glue_streaming_job.add_dependency(grant_lake_formation_permissions)

app.synth()
