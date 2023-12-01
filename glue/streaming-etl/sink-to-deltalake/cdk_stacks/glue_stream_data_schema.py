#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue
)
from constructs import Construct


class GlueStreamDataSchemaStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, kinesis_stream, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    glue_kinesis_table = self.node.try_get_context('glue_kinesis_table')
    database_name = glue_kinesis_table['database_name']
    table_name = glue_kinesis_table['table_name']
    columns = glue_kinesis_table.get('columns', [])

    cfn_database = aws_glue.CfnDatabase(self, "GlueCfnDatabaseOnKinesis",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
        name=database_name
      )
    )
    cfn_database.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cfn_table = aws_glue.CfnTable(self, "GlueCfnTableOnKinesis",
      catalog_id=cdk.Aws.ACCOUNT_ID,
      database_name=database_name,
      table_input=aws_glue.CfnTable.TableInputProperty(
        name=table_name,
        parameters={"classification": "json"},
        storage_descriptor=aws_glue.CfnTable.StorageDescriptorProperty(
          columns=columns,
          input_format="org.apache.hadoop.mapred.TextInputFormat",
          location=kinesis_stream.stream_name,
          output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
          parameters={
            "streamARN": kinesis_stream.stream_arn,
            "typeOfData": "kinesis"
          },
          serde_info=aws_glue.CfnTable.SerdeInfoProperty(
            serialization_library="org.openx.data.jsonserde.JsonSerDe"
          )
        ),
        table_type="EXTERNAL_TABLE"
      )
    )

    cfn_table.add_dependency(cfn_database)
    cfn_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

    cdk.CfnOutput(self, f'{self.stack_name}_GlueDatabaseName', value=cfn_table.database_name)
