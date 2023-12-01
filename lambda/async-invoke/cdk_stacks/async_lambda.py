#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_events,
  aws_events_targets,
  aws_iam,
  aws_lambda,
  aws_lambda_destinations,
  aws_lambda_event_sources,
  aws_logs,
  aws_sns
)
from constructs import Construct


class LambdaAsyncInvokeStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    ASYNC_CALLEE_LAMBDA_FN_NAME = "LambdaAsyncCallee"
    async_callee_lambda_fn = aws_lambda.Function(self, "LambdaAsyncCallee",
      runtime=aws_lambda.Runtime.PYTHON_3_7,
      function_name="LambdaAsyncCallee",
      handler="lambda_aync_callee.lambda_handler",
      description="Lambda function asynchrously invoked by LambdaAsyncCaller",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      timeout=cdk.Duration.minutes(5)
    )

    log_group = aws_logs.LogGroup(self, "LambdaAsyncCalleeLogGroup",
      #XXX: Circular dependency between resources occurs
      # if aws_lambda.Function.function_name is used
      # instead of literal name of lambda function such as "LambdaAsyncCallee"
      log_group_name="/aws/lambda/{}".format(ASYNC_CALLEE_LAMBDA_FN_NAME),
      retention=aws_logs.RetentionDays.THREE_DAYS,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )
    log_group.grant_write(async_callee_lambda_fn)

    event_bus = aws_events.EventBus(self, "EventBusForLambda",
      event_bus_name="EventBusForLambdaDestinations",
    )
    event_bus.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    log_group = aws_logs.LogGroup(self, "EventBusLogGroup",
      log_group_name="/aws/events/{}".format(event_bus.event_bus_name),
      retention=aws_logs.RetentionDays.THREE_DAYS,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    event_rule = aws_events.Rule(self, "EventRuleForLambdaDestinations",
      rule_name="EventRuleForLambdaDestinations",
      event_bus=event_bus,
      event_pattern={
        "account": [self.account]
      }
    )
    event_rule.add_target(aws_events_targets.CloudWatchLogGroup(log_group))
    event_rule.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    CALLER_LAMBDA_FN_NAME = "LambdaAsyncCaller"
    caller_lambda_fn = aws_lambda.Function(self, "LambdaAsyncCaller",
      runtime=aws_lambda.Runtime.PYTHON_3_7,
      function_name="LambdaAsyncCaller",
      handler="lambda_caller.lambda_handler",
      description="Asynchronusly call lambda function",
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/python')),
      timeout=cdk.Duration.minutes(5),
      #XXX: Uncomments out if you want to use different lambda function version
      # current_version_options=aws_lambda.VersionOptions(
      #   on_success=aws_lambda_destinations.LambdaDestination(async_callee_lambda_fn, response_only=False),
      #   on_failure=aws_lambda_destinations.EventBridgeDestination(event_bus),
      #   max_event_age=cdk.Duration.hours(6), # Minimum: 60 seconds, Maximum: 6 hours, Default: 6 hours
      #   retry_attempts=0 # Minimum: 0, Maximum: 2, Default: 2
      # ),
      on_success=aws_lambda_destinations.LambdaDestination(async_callee_lambda_fn, response_only=False),
      on_failure=aws_lambda_destinations.EventBridgeDestination(event_bus),
      max_event_age=cdk.Duration.hours(6), # Minimum: 60 seconds Maximum: 6 hours, Default: 6 hours
      #XXX: Set retry_attempts to 0 in order to invoke other lambda function as soon as a error occurred
      retry_attempts=0 # Minimum: 0, Maximum: 2, Default: 2
    )

    sns_topic = aws_sns.Topic(self, 'SnsTopicForLambda',
      topic_name='LambdaSourceEvent',
      display_name='lambda source event'
    )
    caller_lambda_fn.add_event_source(aws_lambda_event_sources.SnsEventSource(sns_topic))

    caller_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(partition="aws", service="lambda",
        region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID, resource="function",
        resource_name="{}*".format(async_callee_lambda_fn.function_name), arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["lambda:InvokeFunction"]))

    caller_lambda_fn.add_to_role_policy(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[event_bus.event_bus_arn],
      actions=["events:PutEvents"]))

    log_group = aws_logs.LogGroup(self, "LambdaAsyncCallerLogGroup",
      #XXX: Circular dependency between resources occurs
      # if aws_lambda.Function.function_name is used
      # instead of literal name of lambda function such as "LambdaAsyncCaller"
      log_group_name="/aws/lambda/{}".format(CALLER_LAMBDA_FN_NAME),
      retention=aws_logs.RetentionDays.THREE_DAYS,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )
    log_group.grant_write(caller_lambda_fn)

    cdk.CfnOutput(self, 'SNSTopicName',
      value=sns_topic.topic_name,
      export_name=f'{self.stack_name}-SNSTopicName')
    cdk.CfnOutput(self, 'SNSTopicArn',
      value=sns_topic.topic_arn,
      export_name=f'{self.stack_name}-SNSTopicArn')
