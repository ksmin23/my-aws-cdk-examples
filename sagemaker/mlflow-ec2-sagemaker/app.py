#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  S3Stack,
  AuroraMysqlStack,
  MLflowOnEC2InstanceStack,
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

rds_stack = AuroraMysqlStack(app, "MLflowRDSStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
rds_stack.add_dependency(s3_stack)

mlflow_ec2_instance_stack = MLflowOnEC2InstanceStack(app, "MLflowOnEC2InstanceStack",
  vpc_stack.vpc,
  s3_stack.artifact_bucket,
  rds_stack.sg_rds_client,
  rds_stack.database_endpoint,
  rds_stack.database_secret,
  rds_stack.database_name,
  env=AWS_ENV
)
mlflow_ec2_instance_stack.add_dependency(rds_stack)

sagemaker_studio_stack = SageMakerStudioStack(app, "MLflowSageMakerStudioStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
sagemaker_studio_stack.add_dependency(mlflow_ec2_instance_stack)

app.synth()
