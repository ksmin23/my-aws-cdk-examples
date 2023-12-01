#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_lambda,
  aws_events,
  aws_events_targets,
)
from constructs import Construct
from cdk_lambda_powertools_python_layer import LambdaPowertoolsLayer


class ScheduledLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    powertools_layer = LambdaPowertoolsLayer(self, 'PowertoolsLayer')

    lambda_fn = aws_lambda.Function(self, "ScheduledLambdaTest",
      runtime=aws_lambda.Runtime.PYTHON_3_7,
      function_name="ScheduledLambdaTest",
      handler="scheduled_lambda_test.lambda_handler",
      description="Scheduled Lambda Test",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      timeout=cdk.Duration.minutes(5),
      layers=[powertools_layer]
    )

    # Create EventBridge rule that will execute our Lambda every 2 minutes
    schedule = aws_events.Rule(self, 'ScheduledLambdaTest-schedule',
      schedule=aws_events.Schedule.expression('rate(2 minutes)')
    )

    #Set the target of our EventBridge rule to our Lambda function
    schedule.add_target(aws_events_targets.LambdaFunction(lambda_fn))
