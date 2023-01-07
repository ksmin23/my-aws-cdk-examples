#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  FSxLustreStack,
  FSxLustreDataRepoAssociationStack,
  SageMakerStudioStack
)

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

vpc_stack = VpcStack(app, "SageMakerFSxLustreVPC",
  env=AWS_ENV)

sagemaker_studio_stack = SageMakerStudioStack(app, "SageMakerStudioWithFSxLustre",
  vpc_stack.vpc,
  env=AWS_ENV)
sagemaker_studio_stack.add_dependency(vpc_stack)

fsx_lustre_stack = FSxLustreStack(app, "FSxLustreForSageMakerStack",
  vpc_stack.vpc,
  env=AWS_ENV)
fsx_lustre_stack.add_dependency(sagemaker_studio_stack)

fsx_lustre_data_repo_stack = FSxLustreDataRepoAssociationStack(app, "FSxLustreDataRepositoryForSageMakerStack",
  fsx_lustre_stack.file_system_id,
  env=AWS_ENV)
fsx_lustre_data_repo_stack.add_dependency(fsx_lustre_stack)

app.synth()
