#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

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

    OPEN_SERACH_IAM_USER = self.node.try_get_context("opensearch_iam_user")
    IAM_USER_NAME = OPEN_SERACH_IAM_USER["user_name"]
    IAM_USER_INITIAL_PASSWORD = OPEN_SERACH_IAM_USER["initial_password"]

    user = aws_iam.User(self, "OpsAdminUser",
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('IAMUserChangePassword'),
      ],
      password=cdk.SecretValue.unsafe_plain_text(IAM_USER_INITIAL_PASSWORD),
      password_reset_required=True,
      user_name=IAM_USER_NAME)

    user.add_to_policy(aws_iam.PolicyStatement(**{
      "sid": "UsingOpenSearchServerlessIntheConsole",
      "effect": aws_iam.Effect.ALLOW,
      "resources": ["*"],
      "actions": [
        "aoss:ListCollections",
        "aoss:BatchGetCollection",
        "aoss:ListAccessPolicies",
        "aoss:ListSecurityConfigs",
        "aoss:ListSecurityPolicies",
        "aoss:ListTagsForResource",
        "aoss:ListVpcEndpoints",
        "aoss:GetAccessPolicy",
        "aoss:GetAccountSettings",
        "aoss:GetSecurityConfig",
        "aoss:GetSecurityPolicy"
      ]
    }))

    user.add_to_policy(aws_iam.PolicyStatement(**{
      "sid": "AdministeringOpenSearchServerlessCollections1",
      "effect": aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="aoss",
                      region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID,
                      resource="collection", arn_format=cdk.ArnFormat.SLASH_RESOURCE_NAME,
                      resource_name="*")],
      "actions": [
        "aoss:CreateCollection",
        "aoss:DeleteCollection",
        "aoss:UpdateCollection"
      ]
    }))

    user.add_to_policy(aws_iam.PolicyStatement(**{
      "sid": "AdministeringOpenSearchServerlessCollections2",
      "effect": aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [ "*" ],
      "actions": [
         "aoss:BatchGetCollection",
         "aoss:ListCollections",
         "aoss:CreateAccessPolicy",
         "aoss:CreateSecurityPolicy"
      ]
    }))

    # Using data-plane policies
    user.add_to_policy(aws_iam.PolicyStatement(**{
      "sid": "OpenSearchServerlessDataPlaneAccess1",
      "effect": aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="aoss",
                      region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID,
                      resource="collection", arn_format=cdk.ArnFormat.SLASH_RESOURCE_NAME,
                      resource_name="*")],
      "actions": [
        "aoss:APIAccessAll"
      ]
    }))

    user.add_to_policy(aws_iam.PolicyStatement(**{
      "sid": "OpenSearchServerlessDataPlaneAccess2",
      "effect": aws_iam.Effect.ALLOW,
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}{resource-name}
      "resources": [self.format_arn(service="aoss",
                      region=cdk.Aws.REGION, account=cdk.Aws.ACCOUNT_ID,
                      resource="dashboards", arn_format=cdk.ArnFormat.SLASH_RESOURCE_NAME,
                      resource_name="default")],
      "actions": [
        "aoss:DashboardsAccessAll"
      ]
    }))

    access_key = aws_iam.AccessKey(self, "OpsAdminUserAccessKey", user=user)

    secret = aws_secretsmanager.Secret(self, "OpsAdminUserSecret",
      secret_name="opss-user",
      secret_object_value={
        "username": cdk.SecretValue.unsafe_plain_text(user.user_name),
        "access_key_id": cdk.SecretValue.unsafe_plain_text(access_key.access_key_id),
        "secret_access_key": access_key.secret_access_key
      },
      removal_policy=cdk.RemovalPolicy.DESTROY
    )

    user.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
    access_key.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    self.user_arn = user.user_arn
    self.user_name = user.user_name

    cdk.CfnOutput(self, 'UserName',
      value=self.user_name,
      export_name=f'{self.stack_name}-UserName')
    cdk.CfnOutput(self, 'UserSecretName',
      value=secret.secret_name,
      export_name=f'{self.stack_name}-UserSecretName')
