#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  MskStack,
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

vpc_stack = VpcStack(app, 'KafkaToIcebergStackVpc',
  env=APP_ENV
)

msk_stack = MskStack(app, 'KafkaAsGlueStreamingJobDataSource',
  vpc_stack.vpc,
  env=APP_ENV
)
msk_stack.add_dependency(vpc_stack)

kafka_client_ec2_stack = KafkaClientEC2InstanceStack(app, 'KafkaClientEC2Instance',
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  msk_stack.msk_cluster_name,
  env=APP_ENV
)
kafka_client_ec2_stack.add_dependency(msk_stack)

glue_msk_connection = GlueMSKConnectionStack(app, 'GlueMSKConnection',
  vpc_stack.vpc,
  msk_stack.sg_msk_client,
  env=APP_ENV
)
glue_msk_connection.add_dependency(msk_stack)

glue_job_role = GlueJobRoleStack(app, 'GlueStreamingMSKtoIcebergJobRole')
glue_job_role.add_dependency(msk_stack)

glue_database = GlueCatalogDatabaseStack(app, 'GlueIcebergeDatabase')

grant_lake_formation_permissions = DataLakePermissionsStack(app, 'GrantLFPermissionsOnGlueJobRole',
  glue_job_role.glue_job_role
)
grant_lake_formation_permissions.add_dependency(glue_database)
grant_lake_formation_permissions.add_dependency(glue_job_role)

glue_streaming_job = GlueStreamingJobStack(app, 'GlueStreamingJobMSKtoIceberg',
  glue_job_role.glue_job_role,
  glue_msk_connection.msk_connection_info
)
glue_streaming_job.add_dependency(grant_lake_formation_permissions)

app.synth()
