#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_cognito
)
from constructs import Construct


class CognitoUserPoolStack(Stack):

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

    self.user_pool = user_pool


    cdk.CfnOutput(self, 'UserPoolId',
      value=user_pool.user_pool_id,
      export_name=f'{self.stack_name}-UserPoolId')
    cdk.CfnOutput(self, 'UserPoolClientId',
      value=user_pool_client.user_pool_client_id,
      export_name=f'{self.stack_name}-UserPoolClientId')
