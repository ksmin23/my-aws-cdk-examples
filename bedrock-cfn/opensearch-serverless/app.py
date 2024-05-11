#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import os

import aws_cdk as cdk

from cdk_stacks import (
  KnowledgeBaseRoleStack,
  KnowledgeBaseforBedrockStack,
  KnowledgeBaseDataSourceStack,
  OpsServerlessVectorSearchStack,
  OpenSearchLambdaLayerStack,
  OpenSearchIndexCreationLambdaStack,
  CustomResourceStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

kb_role_for_bedrock_stack = KnowledgeBaseRoleStack(app, "KBforBedrockRoleStack",
  env=AWS_ENV)

opss_vectorstore_stack = OpsServerlessVectorSearchStack(app, "OpsServerlessVectorStoreStack",
  kb_role_arn=kb_role_for_bedrock_stack.kb_role_arn,
  env=AWS_ENV)
opss_vectorstore_stack.add_dependency(kb_role_for_bedrock_stack)

lambda_layer_stack = OpenSearchLambdaLayerStack(app, "OpenSearchPySDKLambdaLayerStack",
  env=AWS_ENV)
lambda_layer_stack.add_dependency(opss_vectorstore_stack)

lambda_function_stack = OpenSearchIndexCreationLambdaStack(app, "OpenSearchIndexCreationLambdaStack",
  lambda_layer=lambda_layer_stack.lambda_layer,
  opensearch_endpoint=opss_vectorstore_stack.opensearch_collection_endpoint,
  env=AWS_ENV)
lambda_function_stack.add_dependency(lambda_layer_stack)

custom_resource_stack = CustomResourceStack(app, "OpenSearchIndexCreationStack",
  lambda_function_stack.lambda_function_arn,
  opss_vectorstore_stack.opensearch_collection_endpoint,
  opss_vectorstore_stack.opensearch_data_access_policy_name,
  env=AWS_ENV)
custom_resource_stack.add_dependency(lambda_function_stack)

kb_for_bedrock_stack = KnowledgeBaseforBedrockStack(app, "KBforBedrockStack",
  kb_role_arn=kb_role_for_bedrock_stack.kb_role_arn,
  opensearch_collection_arn=opss_vectorstore_stack.opensearch_collection_arn,
  env=AWS_ENV)
kb_for_bedrock_stack.add_dependency(custom_resource_stack)

kb_data_source_stack = KnowledgeBaseDataSourceStack(app, "KBDataSourceStack",
  knowledge_base_id=kb_for_bedrock_stack.knowledge_base_id,
  env=AWS_ENV)
kb_data_source_stack.add_dependency(kb_for_bedrock_stack)

app.synth()
