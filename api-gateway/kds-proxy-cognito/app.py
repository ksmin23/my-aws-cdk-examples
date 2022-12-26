#!/usr/bin/env python3
import os
import json
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Duration,
  Stack,
  aws_apigateway,
  aws_cognito,
  aws_ec2,
  aws_iam,
  aws_kinesis,
)
from constructs import Construct

random.seed(31)

class KdsProxyWithCognitoStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    KINESIS_STREAM_NAME = cdk.CfnParameter(self, 'KinesisStreamName',
      type='String',
      description='kinesis data stream name',
      default='PUT-Firehose-{}'.format(''.join(random.sample((string.ascii_letters), k=5)))
    )

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context("vpc_name")
    # vpc = aws_ec2.Vpc.from_lookup(self, "ExistingVPC",
    #   is_default=True,
    #   vpc_name=vpc_name)
    #
    #XXX: To use more than 2 AZs, be sure to specify the account and region on your stack.
    #XXX: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_ec2/Vpc.html
    # vpc = aws_ec2.Vpc(self, "KdsProxyWithCognitoVPC",
    #   max_azs=2,
    #   gateway_endpoints={
    #     "S3": aws_ec2.GatewayVpcEndpointOptions(
    #       service=aws_ec2.GatewayVpcEndpointAwsService.S3
    #     )
    #   }
    # )

    source_kinesis_stream = aws_kinesis.Stream(self, "SourceKinesisStreams",
      retention_period=Duration.hours(24),
      stream_mode=aws_kinesis.StreamMode.ON_DEMAND, 
      stream_name=KINESIS_STREAM_NAME.value_as_string)

    user_pool = aws_cognito.UserPool(self, 'UserPool',
      user_pool_name='UserPoolForApiGateway',
      removal_policy=cdk.RemovalPolicy.DESTROY,
      self_sign_up_enabled=True,
      sign_in_aliases={'email': True},
      auto_verify={'email': True},
      password_policy={
        'min_length': 8,
        'require_lowercase': False,
        'require_digits': False,
        'require_uppercase': False,
        'require_symbols': False,
      },
      account_recovery=aws_cognito.AccountRecovery.EMAIL_ONLY
    )

    user_pool_client = aws_cognito.UserPoolClient(self, 'UserPoolClient',
      user_pool=user_pool,
      auth_flows={
        'admin_user_password': True,
        'user_password': True,
        'custom': True,
        'user_srp': True
      },
      supported_identity_providers=[aws_cognito.UserPoolClientIdentityProvider.COGNITO]
    )

    auth = aws_apigateway.CognitoUserPoolsAuthorizer(self, 'AuthorizerForKdsProxyApi',
      cognito_user_pools=[user_pool]
    )

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
      role_name='APIGatewayRoleToAccessKinesisDataStreams',
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
      rest_api_name="kds-proxy-with-cognito",
      description="An Amazon API Gateway REST API that integrated with an Amazon Kinesis Data Streams.",
      endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
      default_cors_preflight_options={
        "allow_origins": aws_apigateway.Cors.ALL_ORIGINS
      },
      deploy=True,
      deploy_options=aws_apigateway.StageOptions(stage_name="v1"),
      endpoint_export_name="KdsProxyAPIEndpoint"
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
      authorization_type=aws_apigateway.AuthorizationType.COGNITO,
      authorizer=auth,
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
      authorization_type=aws_apigateway.AuthorizationType.COGNITO,
      authorizer=auth,
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
      authorization_type=aws_apigateway.AuthorizationType.COGNITO,
      authorizer=auth,
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
      authorization_type=aws_apigateway.AuthorizationType.COGNITO,
      authorizer=auth,
      method_responses=[aws_apigateway.MethodResponse(status_code='200',
          response_models={
            'application/json': aws_apigateway.Model.EMPTY_MODEL
          }
        ),
        aws_apigateway.MethodResponse(status_code='400'),
        aws_apigateway.MethodResponse(status_code='500')
        ])

    cdk.CfnOutput(self, '{}_KinesisDataStreamName'.format(self.stack_name), 
      value=source_kinesis_stream.stream_name, export_name='KinesisDataStreamName')
    cdk.CfnOutput(self, 'UserPoolId', value=user_pool.user_pool_id)
    cdk.CfnOutput(self, 'UserPoolClientId', value=user_pool_client.user_pool_client_id)


app = cdk.App()
KdsProxyWithCognitoStack(app, "ApiGwKdsProxyWithCognitoStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
