#!/usr/bin/env python3
import os
import json
import random
import string

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_cognito,
  aws_dynamodb,
  aws_iam,
  aws_apigateway
)
from constructs import Construct


class CognitoProtectedDynamoDBApiStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    #XXX: For creating this CDK Stack in the existing VPC,
    # remove comments from the below codes and
    # comments out vpc = aws_ec2.Vpc(..) codes,
    # then pass -c vpc_name=your-existing-vpc to cdk command
    # for example,
    # cdk -c vpc_name=your-existing-vpc syth
    #
    # vpc_name = self.node.try_get_context('vpc_name')
    # vpc = aws_ec2.Vpc.from_lookup(self, 'ExistingVPC',
    #   is_default=True,
    #   vpc_name=vpc_name
    # )

    vpc = aws_ec2.Vpc(self, "ApiGatewayDynamoDBVPC",
      max_azs=2,
      gateway_endpoints={
        "S3": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.S3
        ),
        "DynamoDB": aws_ec2.GatewayVpcEndpointOptions(
          service=aws_ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )
      }
    )

    DDB_TABLE_SUFFIX = ''.join(random.sample((string.ascii_lowercase + string.digits), k=7))
    DDB_TABLE_NAME = "Comments-{}".format(DDB_TABLE_SUFFIX)

    ddb_table = aws_dynamodb.Table(self, "DynamoDbTable",
      table_name=DDB_TABLE_NAME,
      removal_policy=cdk.RemovalPolicy.DESTROY,
      partition_key=aws_dynamodb.Attribute(name="commentId",
        type=aws_dynamodb.AttributeType.STRING),
      time_to_live_attribute="ttl",
      billing_mode=aws_dynamodb.BillingMode.PROVISIONED,
      read_capacity=15,
      write_capacity=5,
    )

    ddb_table.add_global_secondary_index(
      read_capacity=15,
      write_capacity=5,
      index_name="pageId-index",
      partition_key=aws_dynamodb.Attribute(name='pageId', type=aws_dynamodb.AttributeType.STRING),
      projection_type=aws_dynamodb.ProjectionType.ALL
    )

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

    auth = aws_apigateway.CognitoUserPoolsAuthorizer(self, 'AuthorizerForDynamoDBApi',
      cognito_user_pools=[user_pool]
    )

    ddb_access_policy_doc = aws_iam.PolicyDocument()
    ddb_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ddb_table.table_arn],
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
          "TableName": DDB_TABLE_NAME,
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
          "TableName": DDB_TABLE_NAME,
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

    cdk.CfnOutput(self, 'DynamoDBTableName', value=ddb_table.table_name)
    cdk.CfnOutput(self, 'UserPoolId', value=user_pool.user_pool_id)
    cdk.CfnOutput(self, 'UserPoolClientId', value=user_pool_client.user_pool_client_id)


app = cdk.App()
CognitoProtectedDynamoDBApiStack(app, "CognitoProtectedDynamoDBApiStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
