#!/usr/bin/env python3
import os

from cdk_stacks import (
  SageMakerLambdaLayerStack,
  JumpStartModelDeployLambdaStack,
  SageMakerIAMRoleStack,
  CustomResourceStack
)

import aws_cdk as cdk

AWS_ENV = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION'))

app = cdk.App()

lambda_layer_stack = SageMakerLambdaLayerStack(app, "SageMakerPySDKLambdaLayerStack",
  env=AWS_ENV)

sagemaker_exec_iam_role_stack = SageMakerIAMRoleStack(app, "SageMakerExecIAMRoleStack",
  env=AWS_ENV)
sagemaker_exec_iam_role_stack.add_dependency(lambda_layer_stack)

lambda_function_stack = JumpStartModelDeployLambdaStack(app, "SMJumpStartModelDeployLambdaStack",
  lambda_layer_stack.lambda_layer,
  sagemaker_iam_role_arn=sagemaker_exec_iam_role_stack.sagemaker_execution_role_arn,
  env=AWS_ENV)
lambda_function_stack.add_dependency(sagemaker_exec_iam_role_stack)

custom_resource_stack = CustomResourceStack(app, "SMJumpStartModelEndpointStack",
  lambda_function_stack.lambda_function_arn,
  env=AWS_ENV)
custom_resource_stack.add_dependency(lambda_function_stack)

app.synth()
