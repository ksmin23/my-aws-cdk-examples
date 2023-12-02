#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_apigateway
)
from constructs import Construct


class CognitoProtectedDynamoDBApiStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, user_pool, dynamodb_table, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    auth = aws_apigateway.CognitoUserPoolsAuthorizer(self, 'AuthorizerForDynamoDBApi',
      cognito_user_pools=[user_pool]
    )

    ddb_access_policy_doc = aws_iam.PolicyDocument()
    ddb_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [dynamodb_table.table_arn],
      "actions": [
        "dynamodb:DeleteItem",
        "dynamodb:PartiQLInsert",
        "dynamodb:UpdateTimeToLive",
        "dynamodb:BatchWriteItem",
        "dynamodb:PutItem",
        "dynamodb:PartiQLUpdate",
        "dynamodb:UpdateItem",
        "dynamodb:PartiQLDelete"
      ]
    }))

    apigw_dynamodb_role = aws_iam.Role(self, "ApiGatewayRoleForDynamoDB",
      role_name='APIGatewayRoleForDynamoDB',
      assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
      inline_policies={
        'DynamoDBAccessPolicy': ddb_access_policy_doc
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBReadOnlyAccess'),
      ]
    )

    dynamodb_api = aws_apigateway.RestApi(self, "DynamoDBProxyAPI",
      rest_api_name="comments-api",
      description="An Amazon API Gateway REST API that integrated with an Amazon DynamoDB.",
      endpoint_types=[aws_apigateway.EndpointType.REGIONAL],
      default_cors_preflight_options={
        "allow_origins": aws_apigateway.Cors.ALL_ORIGINS
      },
      deploy=True,
      deploy_options=aws_apigateway.StageOptions(stage_name="v1"),
      endpoint_export_name="DynamoDBProxyAPIEndpoint"
    )

    all_resources = dynamodb_api.root.add_resource("comments")
    one_resource = all_resources.add_resource("{pageId}")

    apigw_error_responses = [
      aws_apigateway.IntegrationResponse(status_code="400", selection_pattern="4\d{2}"),
      aws_apigateway.IntegrationResponse(status_code="500", selection_pattern="5\d{2}")
    ]

    apigw_ok_responses = [
      aws_apigateway.IntegrationResponse(
        status_code="200"
      )
    ]

    ddb_put_item_options = aws_apigateway.IntegrationOptions(
      credentials_role=apigw_dynamodb_role,
      integration_responses=[*apigw_ok_responses, *apigw_error_responses],
      request_templates={
        'application/json': json.dumps({
          "TableName": dynamodb_table.table_name,
          "Item": {
            "commentId": {
              "S": "$context.requestId"
            },
            "pageId": {
              "S": "$input.path('$.pageId')"
            },
            "userName": {
              "S": "$input.path('$.userName')"
            },
            "message": {
              "S": "$input.path('$.message')"
            }
          }
        }, indent=2)
      },
      passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
    )

    create_integration = aws_apigateway.AwsIntegration(
      service='dynamodb',
      action='PutItem',
      integration_http_method='POST',
      options=ddb_put_item_options
    )

    method_responses = [
      aws_apigateway.MethodResponse(status_code='200'),
      aws_apigateway.MethodResponse(status_code='400'),
      aws_apigateway.MethodResponse(status_code='500')
    ]

    all_resources.add_method('POST', create_integration,
      method_responses=method_responses,
      authorization_type=aws_apigateway.AuthorizationType.COGNITO,
      authorizer=auth
    )

    get_response_templates = '''
#set($inputRoot = $input.path('$'))
{
  "comments": [
    #foreach($elem in $inputRoot.Items) {
       "commentId": "$elem.commentId.S",
       "userName": "$elem.userName.S",
       "message": "$elem.message.S"
     }#if($foreach.hasNext),#end
    #end
  ]
}'''

    ddb_query_item_options = aws_apigateway.IntegrationOptions(
      credentials_role=apigw_dynamodb_role,
      integration_responses=[
        aws_apigateway.IntegrationResponse(
          status_code="200",
          response_templates={
            'application/json': get_response_templates
          }
        ),
        *apigw_error_responses
      ],
      request_templates={
        'application/json': json.dumps({
          "TableName": dynamodb_table.table_name,
          "IndexName": "pageId-index",
          "KeyConditionExpression": "pageId = :v1",
          "ExpressionAttributeValues": {
            ":v1": {
              "S": "$input.params('pageId')"
            }
          }
        }, indent=2)
      },
      passthrough_behavior=aws_apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES
    )

    get_integration = aws_apigateway.AwsIntegration(
      service='dynamodb',
      action='Query',
      integration_http_method='POST',
      options=ddb_query_item_options
    )

    one_resource.add_method('GET', get_integration,
      method_responses=method_responses,
      authorization_type=aws_apigateway.AuthorizationType.COGNITO,
      authorizer=auth
    )


    cdk.CfnOutput(self, 'RestApiEndpointUrl',
      value=dynamodb_api.url,
      export_name=f'{self.stack_name}-RestApiEndpointUrl')
