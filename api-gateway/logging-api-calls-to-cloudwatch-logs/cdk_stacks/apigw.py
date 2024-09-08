#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_apigateway,
  aws_iam,
  aws_logs,
)
from constructs import Construct


class LoggingApiCallsToCloudwatchLogsStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, lambda_fn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    FIREHOSE_NAME = self.node.try_get_context('firehose_name')
    assert not FIREHOSE_NAME.startswith('amazon-apigateway-')

    firehose_arn = f'arn:aws:firehose:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:deliverystream/{FIREHOSE_NAME}'

    cwl_write_to_firehose_policy_doc = aws_iam.PolicyDocument(
      statements=[aws_iam.PolicyStatement(
        effect=aws_iam.Effect.ALLOW,
        resources=[firehose_arn],
        actions=["firehose:PutRecord"]
      )]
    )

    cwl_to_firehose_role = aws_iam.Role(self, 'CWLtoKinesisFirehoseRole',
      role_name="CWLtoKinesisFirehoseRole",
      assumed_by=aws_iam.ServicePrincipal(f"logs.amazonaws.com",
        conditions={
          "StringLike": {
            "aws:SourceArn": f"arn:aws:logs:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:*"
          }
        },
        region=cdk.Aws.REGION
      ),
      inline_policies={
        "firehose_write_policy": cwl_write_to_firehose_policy_doc
      }
    )

    #XXX: CloudWatch Logs role ARN must be set in account settings to enable logging
    cloudwatch_role = aws_iam.Role(self, 'ApiGatewayCloudWatchRole',
      assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonAPIGatewayPushToCloudWatchLogs')
      ]
    )
    cloudwatch_role.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    #XXX: CloudWatch Logs role ARN must be set in account settings to enable logging
    apigw_account = aws_apigateway.CfnAccount(self, 'ApiGatewayAccount',
      cloud_watch_role_arn=cloudwatch_role.role_arn
    )
    apigw_account.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    random_gen_api_log_group = aws_logs.LogGroup(self, 'RandomGenApiLogs')

    cwl_subscription_filter = aws_logs.CfnSubscriptionFilter(self, 'CWLSubscriptionFilter',
      destination_arn=firehose_arn,
      filter_pattern="",
      log_group_name=random_gen_api_log_group.log_group_name,
      role_arn=cwl_to_firehose_role.role_arn
    )

    #XXX: Using aws_apigateway.AccessLogFormat.custom(json.dumps({..}))
    # or aws_apigateway.AccessLogFormat.json_with_standard_fields()
    # make json's all attributes string data type even if they are numbers
    # So, it's better to define access log format in the string like this.
    # Don't forget the new line to make JSON Lines.
    access_log_format = '{"requestId": "$context.requestId",\
 "ip": "$context.identity.sourceIp",\
 "user": "$context.identity.user",\
 "requestTime": $context.requestTimeEpoch,\
 "httpMethod": "$context.httpMethod",\
 "resourcePath": "$context.resourcePath",\
 "status": $context.status,\
 "protocol": "$context.protocol",\
 "responseLength": $context.responseLength}\n'

    random_strings_rest_api = aws_apigateway.LambdaRestApi(self, 'RandomStringsApi',
      rest_api_name="random-strings",
      handler=lambda_fn,
      proxy=False,
      deploy=True,
      deploy_options=aws_apigateway.StageOptions(stage_name='prod',
        data_trace_enabled=True,
        logging_level=aws_apigateway.MethodLoggingLevel.INFO,
        metrics_enabled=True,
        #XXX: You can't use Kinesis Data Firehose as the access_log_destination
        access_log_destination=aws_apigateway.LogGroupLogDestination(random_gen_api_log_group),
        access_log_format=aws_apigateway.AccessLogFormat.custom(access_log_format)
      ),
      endpoint_export_name='RestApiEndpoint'
    )

    random_gen = random_strings_rest_api.root.add_resource('random')
    random_strings_gen = random_gen.add_resource('strings')
    random_strings_gen.add_method('GET',
      aws_apigateway.LambdaIntegration(
        handler=lambda_fn
      )
    )


    cdk.CfnOutput(self, 'RestApiAccessLogToFirehoseARN',
      value=firehose_arn,
      export_name=f'{self.stack_name}-FirehoseARN')
    cdk.CfnOutput(self, 'RestApiAccessLogGroupName',
      value=random_gen_api_log_group.log_group_name,
      export_name=f'{self.stack_name}-LogGroupName')
    cdk.CfnOutput(self, 'RestApiEndpointUrl',
      value=random_strings_rest_api.url,
      export_name=f'{self.stack_name}-RestApiEndpointUrl')
