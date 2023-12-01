#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  MskServerlessStack,
  KafkaClientEC2InstanceStack,
  GlueJobRoleStack,
  GlueMSKConnectionStack,
  GlueCatalogDatabaseStack,
  GlueStreamingJobStack,
  DataLakePermissionsStack
)


APP_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, 'MSKServerlessToIcebergStackVpc',
  env=APP_ENV
)

msk_stack = MskServerlessStack(app, 'MSKServerlessAsGlueStreamingJobDataSource',
  vpc_stack.vpc,
  env=APP_ENV
)
msk_stack.add_dependency(vpc_stack)

kafka_client_ec2_stack = KafkaClientEC2InstanceStack(app, 'MSKServerlessClientEC2Instance',
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  msk_stack.msk_cluster_name,
  env=APP_ENV
)
kafka_client_ec2_stack.add_dependency(msk_stack)

glue_msk_connection = GlueMSKConnectionStack(app, 'GlueMSKServerlessConnection',
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  env=APP_ENV
)
glue_msk_connection.add_dependency(msk_stack)

glue_job_role = GlueJobRoleStack(app, 'GlueStreamingMSKServerlessToIcebergJobRole',
  msk_stack.msk_cluster_name,
)
glue_job_role.add_dependency(msk_stack)

glue_database = GlueCatalogDatabaseStack(app, 'GlueIcebergeDatabase')

grant_lake_formation_permissions = DataLakePermissionsStack(app, 'GrantLFPermissionsOnGlueJobRole',
  glue_job_role.glue_job_role
)
grant_lake_formation_permissions.add_dependency(glue_database)
grant_lake_formation_permissions.add_dependency(glue_job_role)

glue_streaming_job = GlueStreamingJobStack(app, 'GlueStreamingJobMSKServerlessToIceberg',
  glue_job_role.glue_job_role,
  glue_msk_connection.msk_connection_info
)
glue_streaming_job.add_dependency(grant_lake_formation_permissions)

app.synth()
