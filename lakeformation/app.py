#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  GlueCatalogDatabaseStack,
  JobRoleStack,
  DataLakePermissionsStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

glue_databases = GlueCatalogDatabaseStack(app, 'GlueDatabases')

job_role = JobRoleStack(app, "LakeFormationJobRole")

grant_permissions = DataLakePermissionsStack(app, "LakeFormationPermissions",
  job_role.role
)

app.synth()
