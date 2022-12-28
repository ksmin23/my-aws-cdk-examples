#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_secretsmanager,
)
from constructs import Construct


class OpsAdminIAMUserStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    user = aws_iam.User(self, "OpsAdminUser",
      user_name='opss-user')
    access_key = aws_iam.AccessKey(self, "OpsAdminUserAccessKey", user=user)
    secret = aws_secretsmanager.Secret(self, "OpsAdminUserSecret",
      secret_name="opss-user",
      secret_string_value=access_key.secret_access_key,
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    user.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
    access_key.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    self.user_arn = user.user_arn
    self.user_name = user.user_name

    cdk.CfnOutput(self, f'{self.stack_name}-UserName', value=self.user_name)

