#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  KdsStack,
  GlueJobRoleStack,
  GlueStreamDataSchemaStack,
  GlueStreamingJobStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

kds_stack = KdsStack(app, 'KinesisStreamAsGlueStreamingJobDataSource')

glue_job_role = GlueJobRoleStack(app, 'GlueStreamingSinkToIcebergJobRole')
glue_job_role.add_dependency(kds_stack)

glue_stream_schema = GlueStreamDataSchemaStack(app, 'GlueSchemaOnKinesisStream',
  kds_stack.kinesis_stream,
  glue_job_role.glue_job_role
)
glue_stream_schema.add_dependency(glue_job_role)

glue_streaming_job = GlueStreamingJobStack(app, 'GlueStreamingSinkToIceberg',
  glue_job_role.glue_job_role
)
glue_streaming_job.add_dependency(glue_stream_schema)

app.synth()
