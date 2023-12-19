#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
)
from constructs import Construct


class KinesisFirehoseRoleStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, s3_bucket_arn, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    firehose_config = self.node.try_get_context('firehose')
    OPENSEARCH_INDEX_NAME = firehose_config['opensearch_index_name']

    firehose_role_policy_doc = aws_iam.PolicyDocument()
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [s3_bucket_arn, "{}/*".format(s3_bucket_arn)],
      "actions": ["s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"]
    }))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["ec2:DescribeVpcs",
        "ec2:DescribeVpcAttribute",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "ec2:CreateNetworkInterface",
        "ec2:CreateNetworkInterfacePermission",
        "ec2:DeleteNetworkInterface"]
    ))

    firehose_log_group_name = f"/aws/kinesisfirehose/{OPENSEARCH_INDEX_NAME}"
    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      #XXX: The ARN will be formatted as follows:
      # arn:{partition}:{service}:{region}:{account}:{resource}{sep}}{resource-name}
      resources=[self.format_arn(service="logs", resource="log-group",
        resource_name="{}:log-stream:*".format(firehose_log_group_name), arn_format=cdk.ArnFormat.COLON_RESOURCE_NAME)],
      actions=["logs:PutLogEvents"]
    ))

    firehose_role_policy_doc.add_statements(aws_iam.PolicyStatement(**{
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

    firehose_role = aws_iam.Role(self, "KinesisFirehoseServiceRole",
      role_name=f"KinesisFirehoseServiceRole-{self.stack_name}",
      assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
      #XXX: use inline_policies to work around https://github.com/aws/aws-cdk/issues/5221
      inline_policies={
        "firehose_role_policy": firehose_role_policy_doc
      }
    )

    self.firehose_role_arn = firehose_role.role_arn
    self.firehose_role_name = firehose_role.role_name

    cdk.CfnOutput(self, 'FirehoseRoleArn',
      value=self.firehose_role_arn,
      export_name=f'{self.stack_name}-FirehoseRoleArn')
    cdk.CfnOutput(self, 'FirehoseRoleName',
      value=self.firehose_role_name,
      export_name=f'{self.stack_name}-FirehoseRoleName')
