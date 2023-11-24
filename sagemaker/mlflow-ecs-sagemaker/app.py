#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  S3Stack,
  AuroraMysqlClusterStack,
  MLflowECSFargateStack,
  SageMakerStudioStack,
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "MLflowVpcStack",
  env=AWS_ENV)

s3_stack = S3Stack(app, "MLflowS3ArtifactsStack",
  env=AWS_ENV
)
s3_stack.add_dependency(vpc_stack)

rds_stack = AuroraMysqlClusterStack(app, "MLflowRDSStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
rds_stack.add_dependency(s3_stack)

mlflow_ecs_fargate_stack = MLflowECSFargateStack(app, "MLflowOnECSFargateStack",
  vpc_stack.vpc,
  s3_stack.artifact_bucket,
  rds_stack.sg_rds_client,
  rds_stack.database_secret,
  rds_stack.database_name,
  env=AWS_ENV
)
mlflow_ecs_fargate_stack.add_dependency(rds_stack)

sagemaker_studio_stack = SageMakerStudioStack(app, "MLflowSageMakerStudioStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
sagemaker_studio_stack.add_dependency(mlflow_ecs_fargate_stack)

app.synth()
