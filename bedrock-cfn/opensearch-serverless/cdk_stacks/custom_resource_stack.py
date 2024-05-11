#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
)
from constructs import Construct


class CustomResourceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
               cr_provider_lambda_arn, opensearch_endpoint, opensearch_data_access_policy_name,
               **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    bedrock_kb_configuration = self.node.try_get_context('knowledge_base_for_bedrock')
    opensearch_serverless_configuration = bedrock_kb_configuration['storage_configuration']['opensearch_serverless_configuration']
    opensearch_index_name = opensearch_serverless_configuration['vector_index_name']

    knowledge_base_configuration = bedrock_kb_configuration['knowledge_base_configuration']['vector_knowledge_base_configuration']
    embedding_model_arn = knowledge_base_configuration['embedding_model_arn']
    embedding_model_id = embedding_model_arn.split(':foundation-model/')[-1]

    cdk.CustomResource(self, "OSSIndexCreationCustomResource",
      service_token=cr_provider_lambda_arn,
      properties={
        'opensearch_endpoint': opensearch_endpoint,
        'data_access_policy_name': opensearch_data_access_policy_name,
        'index_name': opensearch_index_name,
        'embedding_model_id': embedding_model_id
      }
    )
