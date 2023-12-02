#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json
import random
import string
from datetime import datetime

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_apigateway,
  aws_iam
)
from constructs import Construct

random.seed(47)

class KdsProxyStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    apigw_kds_access_role_policy_doc = aws_iam.PolicyDocument()
    apigw_kds_access_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "kinesis:DescribeStream",
        "kinesis:PutRecord",
        "kinesis:PutRecords"]
    }))

    apigw_kds_role = aws_iam.Role(self, "APIGatewayRoleToAccessKinesisDataStreams",
      role_name=f"APIGatewayRoleToAccessKinesisDataStreams-{datetime.utcnow().strftime('%Y%m%d')}",
      assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
      inline_policies={
        'KinesisWriteAccess': apigw_kds_access_role_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonKinesisReadOnlyAccess')
      ]
    )

    #XXX: Start to create an API as a Kinesis proxy
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html#api-gateway-create-api-as-kinesis-proxy
    kds_proxy_api = aws_apigateway.RestApi(self, "KdsProxyAPI",
      rest_api_name="kds-proxy",
      description="An Amazon API Gateway REST API that integrated with an Amazon Kinesis Data Streams.",
      endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
      default_cors_preflight_options={
        "allow_origins": aws_apigateway.Cors.ALL_ORIGINS
      },
      deploy=True,
      deploy_options=aws_apigateway.StageOptions(stage_name="v1"),
      endpoint_export_name="KdsProxyAPIEndpoint-{}".format(''.join(random.sample(string.ascii_letters, k=3)))
    )

    apigw_error_responses = [
      aws_apigateway.IntegrationResponse(status_code="400", selection_pattern="4\d{2}"),
      aws_apigateway.IntegrationResponse(status_code="500", selection_pattern="5\d{2}")
    ]

    #XXX: GET /streams
    # List Kinesis streams by using the API Gateway console
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html#api-gateway-list-kinesis-streams

    streams_resource = kds_proxy_api.root.add_resource("streams")

    list_streams_options = aws_apigateway.IntegrationOptions(
      credentials_role=apigw_kds_role,
      integration_responses=[
        aws_apigateway.IntegrationResponse(
          status_code="200"
        ),
        *apigw_error_responses
      ],
      request_templates={
        'application/json': '{}'
      },
      passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
    )

    list_streams_integration = aws_apigateway.AwsIntegration(
      service='kinesis',
      action='ListStreams',
      integration_http_method='POST',
      options=list_streams_options
    )

    streams_resource.add_method("GET", list_streams_integration,
      # Default `authorization_type`: - open access unless `authorizer` is specified
      authorization_type=aws_apigateway.AuthorizationType.NONE,
      method_responses=[aws_apigateway.MethodResponse(status_code='200',
          response_models={
            'application/json': aws_apigateway.Model.EMPTY_MODEL
          }
        ),
        aws_apigateway.MethodResponse(status_code='400'),
        aws_apigateway.MethodResponse(status_code='500')
        ])

    #XXX: GET /streams/{stream-name}
    # Describe a stream in Kinesis
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html#api-gateway-create-describe-delete-stream
    one_stream_resource = streams_resource.add_resource("{stream-name}")

    describe_stream_options = aws_apigateway.IntegrationOptions(
      credentials_role=apigw_kds_role,
      integration_responses=[
        aws_apigateway.IntegrationResponse(
          status_code="200"
        ),
        *apigw_error_responses
      ],
      request_templates={
        'application/json': json.dumps({
            "StreamName": "$input.params('stream-name')"
          }, indent=2)
      },
      passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
    )

    describe_stream_integration = aws_apigateway.AwsIntegration(
      service='kinesis',
      action='DescribeStream',
      integration_http_method='POST',
      options=describe_stream_options
    )

    one_stream_resource.add_method("GET", describe_stream_integration,
      # Default `authorization_type`: - open access unless `authorizer` is specified
      authorization_type=aws_apigateway.AuthorizationType.NONE,
      method_responses=[aws_apigateway.MethodResponse(status_code='200',
          response_models={
            'application/json': aws_apigateway.Model.EMPTY_MODEL
          }
        ),
        aws_apigateway.MethodResponse(status_code='400'),
        aws_apigateway.MethodResponse(status_code='500')
        ])

    #XXX: PUT /streams/{stream-name}/record
    # Put a record into a stream in Kinesis
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html#api-gateway-get-and-add-records-to-stream
    record_resource = one_stream_resource.add_resource("record")

    put_record_request_mapping_templates = '''
{
  "StreamName": "$input.params('stream-name')",
  "Data": "$util.base64Encode($input.json('$.Data'))",
  "PartitionKey": "$input.path('$.PartitionKey')"
}
'''

    put_record_options = aws_apigateway.IntegrationOptions(
      credentials_role=apigw_kds_role,
      integration_responses=[
        aws_apigateway.IntegrationResponse(
          status_code="200"
        ),
        *apigw_error_responses
      ],
      request_templates={
        'application/json': put_record_request_mapping_templates
      },
      passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
    )

    put_record_integration = aws_apigateway.AwsIntegration(
      service='kinesis',
      action='PutRecord',
      integration_http_method='POST',
      options=put_record_options
    )

    record_resource.add_method("PUT", put_record_integration,
      # Default `authorization_type`: - open access unless `authorizer` is specified
      authorization_type=aws_apigateway.AuthorizationType.NONE,
      method_responses=[aws_apigateway.MethodResponse(status_code='200',
          response_models={
            'application/json': aws_apigateway.Model.EMPTY_MODEL
          }
        ),
        aws_apigateway.MethodResponse(status_code='400'),
        aws_apigateway.MethodResponse(status_code='500')
        ])


    #XXX: PUT /streams/{stream-name}/records
    # Put records into a stream in Kinesis
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/integrating-api-with-aws-services-kinesis.html#api-gateway-get-and-add-records-to-stream
    records_resource = one_stream_resource.add_resource("records")

    put_records_request_mapping_templates = '''
{
  "StreamName": "$input.params('stream-name')",
  "Records": [
    #foreach($elem in $input.path('$.records'))
      {
        "Data": "$util.base64Encode($elem.data)",
        "PartitionKey": "$elem.partition-key"
      }#if($foreach.hasNext),#end
    #end
  ]
}
'''

    put_records_options = aws_apigateway.IntegrationOptions(
      credentials_role=apigw_kds_role,
      integration_responses=[
        aws_apigateway.IntegrationResponse(
          status_code="200"
        ),
        *apigw_error_responses
      ],
      request_templates={
        'application/json': put_records_request_mapping_templates
      },
      passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
    )

    put_records_integration = aws_apigateway.AwsIntegration(
      service='kinesis',
      action='PutRecords',
      integration_http_method='POST',
      options=put_records_options
    )

    records_resource.add_method("PUT", put_records_integration,
      # Default `authorization_type`: - open access unless `authorizer` is specified
      authorization_type=aws_apigateway.AuthorizationType.NONE,
      method_responses=[aws_apigateway.MethodResponse(status_code='200',
          response_models={
            'application/json': aws_apigateway.Model.EMPTY_MODEL
          }
        ),
        aws_apigateway.MethodResponse(status_code='400'),
        aws_apigateway.MethodResponse(status_code='500')
        ])


    cdk.CfnOutput(self, 'RestApiEndpointUrl',
      value=kds_proxy_api.url,
      export_name=f'{self.stack_name}-RestApiEndpointUrl')