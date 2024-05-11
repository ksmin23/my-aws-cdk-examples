#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_iam,
  aws_lambda
)
from constructs import Construct


class OpenSearchIndexCreationLambdaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
               lambda_layer, opensearch_endpoint, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    bedrock_kb_configuration = self.node.try_get_context('knowledge_base_for_bedrock')
    knowledge_base_configuration = bedrock_kb_configuration['knowledge_base_configuration']['vector_knowledge_base_configuration']
    embedding_model_arn = knowledge_base_configuration['embedding_model_arn']
    embedding_model_id = embedding_model_arn.split(':foundation-model/')[-1]

    opensearch_serverless_policy_doc = aws_iam.PolicyDocument()
    opensearch_serverless_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ "*" ],
      "actions": [
 				"aoss:UpdateAccessPolicy",
				"aoss:GetAccessPolicy",
				"aoss:ListAccessPolicies"
      ]
    }))

    opensearch_serverless_policy_doc.add_statements(aws_iam.PolicyStatement(**{
      "effect": aws_iam.Effect.ALLOW,
      "resources": [ f"arn:aws:aoss:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:collection/*" ],
      "actions": [
 				"aoss:APIAccessAll"
      ]
    }))

    lambda_execution_role = aws_iam.Role(self, 'OSSIndexCreationLambdaRole',
      role_name=f'{self.stack_name}-LambdaExecRole',
      assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
      inline_policies={
        'OSSPolicyForKnowlegeBase': opensearch_serverless_policy_doc,
      },
      managed_policies=[
        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
      ]
    )

    #XXX: AWS Lambda - Defined runtime environment variables
    # https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime
    lambda_fn_env = {
      'EMBEDDING_MODEL_ID': embedding_model_id,
      'OPENSEARCH_ENDPOINT': opensearch_endpoint
    }

    lambda_fn = aws_lambda.Function(self, 'OpenSearchIndexCreationLambdaFn',
      runtime=aws_lambda.Runtime.PYTHON_3_10,
      function_name=f'{self.stack_name}-Function',
      handler='opensearch_index_creation_lambda_fn.lambda_handler',
      description='Create OpenSearch Vector Index for Amazon Bedrock Knowledge Base',
      code=aws_lambda.Code.from_asset('./src/main/python/CustomResourceProvider'),
      layers=[lambda_layer],
      # environment=lambda_fn_env,
      timeout=cdk.Duration.minutes(15),
      memory_size=512,
      role=lambda_execution_role
    )

    self.lambda_function_arn = lambda_fn.function_arn

    cdk.CfnOutput(self, 'LambdaFnName', value=lambda_fn.function_name,
      export_name=f"{self.stack_name}-LambdaFnName")
