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


class RandomStringsLambdaFnStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    random_gen_lambda_fn = aws_lambda.Function(self, 'RandomStringsLambdaFn',
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name='RandomStrings',
      handler='random_strings.lambda_handler',
      description='Function that returns strings randomly generated',
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      timeout=cdk.Duration.minutes(5)
    )

    self.lambda_fn = random_gen_lambda_fn


    cdk.CfnOutput(self, 'LambdaFuncName',
      value=self.lambda_fn.function_name,
      export_name=f'{self.stack_name}-LambdaFuncName')
