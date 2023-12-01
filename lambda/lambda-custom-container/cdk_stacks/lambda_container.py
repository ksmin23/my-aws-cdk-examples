#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_lambda
)

from constructs import Construct


class LambdaCustomContainerStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    lambda_fn = aws_lambda.Function(self, "CustomContainerLambdaFunction",
      code=aws_lambda.Code.from_asset_image(
        directory=os.path.join(os.path.dirname(__file__), '../custom_container/app')
      ),
      #XXX: handler must be `Handler.FROM_IMAGE` when using image asset for Lambda function
      handler=aws_lambda.Handler.FROM_IMAGE,
      #XXX: runtime must be `Runtime.FROM_IMAGE` when using image asset for Lambda function
      runtime=aws_lambda.Runtime.FROM_IMAGE,
      function_name="Hello-KoNLpy",
      description="Lambda function defined in the custom container",
      timeout=cdk.Duration.minutes(5),
      memory_size=5120
    )


    cdk.CfnOutput(self, 'LambdaFuncitonName',
      value=lambda_fn.function_name,
      export_name=f'{self.stack_name}-FunctionName')