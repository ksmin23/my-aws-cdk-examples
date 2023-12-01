#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  KdsStack,
  GlueJobRoleStack,
  GlueStreamDataSchemaStack,
  GlueStreamingJobStack,
  DataLakePermissionsStack
)

APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

kds_stack = KdsStack(app, 'KinesisStreamAsGlueStreamingJobDataSource')

glue_job_role = GlueJobRoleStack(app, 'GlueStreamingSinkToHudiJobRole')
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

glue_streaming_job = GlueStreamingJobStack(app, 'GlueStreamingSinkToHudi',
  glue_job_role.glue_job_role
)
glue_streaming_job.add_dependency(grant_lake_formation_permissions)

app.synth()
