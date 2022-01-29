#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_apigateway,
  aws_cognito,
  aws_lambda
)
from constructs import Construct


class CognitoProtectedApiStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

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

    auth = aws_apigateway.CognitoUserPoolsAuthorizer(self, 'AuthorizerForHelloWorldApi',
      cognito_user_pools=[user_pool]
    )

    helloworld_lambda_fn = aws_lambda.Function(self, 'HelloWorldLambdaFn',
      runtime=aws_lambda.Runtime.PYTHON_3_9,
      function_name="HelloWorldApi",
      handler="helloworld.lambda_handler",
      description='Function that returns 200 with "Hello world!"',
      code=aws_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), 'src/main/python')),
      timeout=cdk.Duration.minutes(5)
    )

    helloworld_lambda_rest_api = aws_apigateway.LambdaRestApi(self, 'HelloWorldLambdaRestApi',
      rest_api_name="helloworld-api",
      handler=helloworld_lambda_fn,
      proxy=False,
      deploy=True,
      deploy_options=aws_apigateway.StageOptions(stage_name="v1"),
      endpoint_export_name='ApiGatewayRestApiEndpoint'
    )

    hello = helloworld_lambda_rest_api.root.add_resource("hello")
    hello.add_method('GET', 
      aws_apigateway.LambdaIntegration(
        handler=helloworld_lambda_fn
      ),
      authorization_type=aws_apigateway.AuthorizationType.COGNITO,
      authorizer=auth
    )

    cdk.CfnOutput(self, 'UserPoolId', value=user_pool.user_pool_id)
    cdk.CfnOutput(self, 'UserPoolClientId', value=user_pool_client.user_pool_client_id)


app = cdk.App()
CognitoProtectedApiStack(app, "CognitoProtectedApiStack", env=cdk.Environment(
  account=os.getenv('CDK_DEFAULT_ACCOUNT'),
  region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
