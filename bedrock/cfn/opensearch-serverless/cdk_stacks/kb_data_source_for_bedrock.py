#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_bedrock
)
from constructs import Construct


class KnowledgeBaseDataSourceStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, knowledge_base_id, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    bedrock_kb_data_source_configuration = self.node.try_get_context('knowledge_base_data_source_configuration')
    s3_configuration = bedrock_kb_data_source_configuration['s3_configuration']
    chunking_configuration = bedrock_kb_data_source_configuration['chunking_configuration']

    cfn_data_source = aws_bedrock.CfnDataSource(self, 'CfnKBDataSource',
      data_source_configuration=aws_bedrock.CfnDataSource.DataSourceConfigurationProperty(
        s3_configuration=aws_bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
          bucket_arn=s3_configuration['bucket_arn'],
        ),
        type='S3'
      ),
      knowledge_base_id=knowledge_base_id,
      name=bedrock_kb_data_source_configuration['name'],
      data_deletion_policy=bedrock_kb_data_source_configuration.get('data_deletion_policy', 'RETAIN'),
      description=bedrock_kb_data_source_configuration.get('description', 'N/A'),
      vector_ingestion_configuration=aws_bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
        chunking_configuration=aws_bedrock.CfnDataSource.ChunkingConfigurationProperty(
          chunking_strategy=chunking_configuration['chunking_strategy'],
          fixed_size_chunking_configuration=aws_bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
            max_tokens=chunking_configuration['fixed_size_chunking_configuration']['max_tokens'],
            overlap_percentage=chunking_configuration['fixed_size_chunking_configuration']['overlap_percentage']
          )
        )
      )
    )

    cdk.CfnOutput(self, 'KnowledgeBaseId',
      value=cfn_data_source.knowledge_base_id,
      export_name=f'{self.stack_name}-KnowledgeBaseId')
    cdk.CfnOutput(self, 'DataSourceName',
      value=cfn_data_source.name,
      export_name=f'{self.stack_name}-DataSourceName')
    cdk.CfnOutput(self, 'DataSourceId',
      value=cfn_data_source.attr_data_source_id,
      export_name=f'{self.stack_name}-DataSourceId')
    cdk.CfnOutput(self, 'DataSourceS3BucketArn',
      value=cfn_data_source.data_source_configuration.s3_configuration.bucket_arn,
      export_name=f'{self.stack_name}-DataSourceS3BucketArn')
