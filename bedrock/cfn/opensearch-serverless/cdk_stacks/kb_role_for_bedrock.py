#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam
)
from constructs import Construct


class KnowledgeBaseRoleStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    kb_data_source_configuration = self.node.try_get_context('knowledge_base_data_source_configuration')
    s3_input_bucket_arn = kb_data_source_configuration['s3_configuration']['bucket_arn']

    kb_foundation_model_policy_doc = aws_iam.PolicyDocument()
    kb_foundation_model_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ f"arn:aws:bedrock:{cdk.Aws.REGION}::foundation-model/*" ],
      "actions": [
        "bedrock:InvokeModel"
      ]
    }))

    kb_oss_policy_doc = aws_iam.PolicyDocument()
    kb_oss_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ f"arn:aws:aoss:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:collection/*" ],
      "actions": [
        "aoss:APIAccessAll"
      ]
    }))

    kb_s3_policy_doc = aws_iam.PolicyDocument()
    kb_s3_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [
        s3_input_bucket_arn,
        f"{s3_input_bucket_arn}/*"
      ],
      "actions": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "conditions": {
        "StringEquals": {
          "aws:ResourceAccount": f"{cdk.Aws.ACCOUNT_ID}"
        }
      }
    }))

    kb_role = aws_iam.Role(self, 'AmazonBedrockExecutionRoleForKnowledgeBase',
      role_name=f"AmazonBedrockExecutionRoleForKB-{self.stack_name}",
      assumed_by=aws_iam.ServicePrincipal('bedrock.amazonaws.com'),
      inline_policies={
        'AmazonBedrockFoundationModelPolicyForKnowledgeBase': kb_foundation_model_policy_doc,
        'AmazonBedrockOSSPolicyForKnowledgeBase': kb_oss_policy_doc,
        'AmazonBedrockS3PolicyForKnowledgeBase': kb_s3_policy_doc,
      }
    )

    self.kb_role_arn = kb_role.role_arn


    cdk.CfnOutput(self, 'KnowledgeBaseRoleArn',
      value=self.kb_role_arn,
      export_name=f'{self.stack_name}-KnowledgeBaseRoleArn')
