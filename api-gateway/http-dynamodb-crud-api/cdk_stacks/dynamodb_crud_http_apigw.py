#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_apigatewayv2_alpha as aws_apigwv2,
  aws_lambda,
)
from aws_cdk.aws_apigatewayv2_integrations_alpha import HttpLambdaIntegration

from constructs import Construct


class DynamoDBCrudHttpApiStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, dynamodb_table, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    dynamodb_config = self.node.try_get_context("dynamodb")
    DDB_TABLE_NAME = dynamodb_config['table_name']

    ddb_crud_api_lambda_fn = aws_lambda.Function(self, f'{self.stack_name}_CrudApiLambdaFn',
      runtime=aws_lambda.Runtime.NODEJS_18_X,
      function_name='http-crud-tutorial-function',
      handler='index.handler',
      description='Lambda function that creates, reads, updates, and deletes items from DynamoDB',
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), '../src/main/nodejs')),
      environment={
        "region": kwargs['env'].region,
        "dynamodb_table": DDB_TABLE_NAME,
      },
      timeout=cdk.Duration.minutes(5)
    )
    dynamodb_table.grant_read_write_data(ddb_crud_api_lambda_fn)

    dynamodb_apigw_integration = HttpLambdaIntegration("DynamoDBApigwIntegration", ddb_crud_api_lambda_fn)

    ddb_crud_http_api = aws_apigwv2.HttpApi(self, "DynamoDBCrudHttpApi",
      api_name="http-crud-tutorial-api",
      description="HTTP CRUD APIs for DynamoDB"
    )

    ddb_crud_http_api.add_routes(
      path="/items",
      methods=[aws_apigwv2.HttpMethod.GET],
      integration=dynamodb_apigw_integration
    )

    ddb_crud_http_api.add_routes(
      path="/items/{id}",
      methods=[aws_apigwv2.HttpMethod.GET],
      integration=dynamodb_apigw_integration
    )

    ddb_crud_http_api.add_routes(
      path="/items",
      methods=[aws_apigwv2.HttpMethod.PUT],
      integration=dynamodb_apigw_integration
    )

    ddb_crud_http_api.add_routes(
      path="/items/{id}",
      methods=[aws_apigwv2.HttpMethod.DELETE],
      integration=dynamodb_apigw_integration
    )

    cdk.CfnOutput(self, f'{self.stack_name}_LambdaFn',
      value=ddb_crud_api_lambda_fn.function_name,
      export_name='HttpLambdaFunctionName')

    cdk.CfnOutput(self, f'{self.stack_name}_ApiEndpoint',
      value=ddb_crud_http_api.api_endpoint,
      export_name='DynamoDBCrudHTTPApiEndpoint')