#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# vim: tabstop=2 shiftwidth=2 softtabstop=2 expandtab

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_glue,
)

from constructs import Construct


class GlueDatabaseForS3TablesStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, s3table_bucket_name, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    firehose_config = self.node.try_get_context("data_firehose_configuration")
    dest_iceberg_table_config = firehose_config.get('destination_iceberg_table_configuration')
    s3table_resource_link_name = dest_iceberg_table_config['database_name']

    s3tables_config = self.node.try_get_context("s3_tables")
    database_name = s3tables_config['namespace_name']
    s3tables_catalog_id = f"{self.account}:s3tablescatalog/{s3table_bucket_name}"

    self.s3table_resource_link = aws_glue.CfnDatabase(self, "CfnGlueDatabase",
      catalog_id=self.account,
      database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
        name=s3table_resource_link_name,
        target_database=aws_glue.CfnDatabase.DatabaseIdentifierProperty(
          catalog_id=s3tables_catalog_id,
          database_name=database_name,
          region=self.region
        )
      )
    )


    cdk.CfnOutput(self, 'S3TablesCatalogId',
      value=s3tables_catalog_id,
      export_name=f'{self.stack_name}-S3TablesCatalogId')
