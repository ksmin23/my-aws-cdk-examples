#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam
)
from constructs import Construct

class JobRoleStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    job_role_policy_doc = aws_iam.PolicyDocument()

    job_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["athena:*"]))

    job_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["s3:Get*",
        "s3:List*",
        "s3:AbortMultipartUpload",
        "s3:PutObject",
      ]))

    job_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["glue:CreateDatabase",
        "glue:DeleteDatabase",
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:UpdateDatabase",
        "glue:CreateTable",
        "glue:DeleteTable",
        "glue:BatchDeleteTable",
        "glue:UpdateTable",
        "glue:GetTable",
        "glue:GetTables",
        "glue:BatchCreatePartition",
        "glue:CreatePartition",
        "glue:DeletePartition",
        "glue:BatchDeletePartition",
        "glue:UpdatePartition",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:BatchGetPartition"
      ]))

    job_role_policy_doc.add_statements(aws_iam.PolicyStatement(
      effect=aws_iam.Effect.ALLOW,
      resources=["*"],
      actions=["lakeformation:GetDataAccess"]))

    job_role = aws_iam.Role(self, 'GlueJobRole',
      role_name='GlueJobRoleExample',
      assumed_by=aws_iam.ServicePrincipal('glue.amazonaws.com'), 
      inline_policies={
        'job_role_policy': job_role_policy_doc
      }
    )

    self.role = job_role

    cdk.CfnOutput(self, f'{self.stack_name}_RoleArn', value=self.role.role_arn)
